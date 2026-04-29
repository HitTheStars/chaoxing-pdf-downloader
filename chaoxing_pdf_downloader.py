#!/usr/bin/env python3
"""
超星学习通 PDF 批量下载器
支持下载那些"没有下载按钮"或"下载按钮被禁用"的 PDF/PPT/Word

原理：
  1. 超星的 PDF 通常托管在 pan-yz.chaoxing.com（云盘预览）
  2. 预览页 HTML 源码里藏有真实的 download 直链（带时效签名）
  3. 部分课程使用 ananas PDF Viewer 嵌入，下载链接藏在 JS 全局变量 window.data 中
  4. 在对应的 iframe 内触发点击，保证 Referer 正确，绕开 403

使用步骤：
  1. python chaoxing_pdf_downloader.py --launch
     在弹出的浏览器中登录超星，然后按 Ctrl+C 结束
  2. 在浏览器里打开课程页面，进入目标章节
  3. python chaoxing_pdf_downloader.py --download

批量下载整门课所有章节：
  python chaoxing_pdf_downloader.py --bulk
"""

import argparse
import os
import platform
import re
import sys
import time
from urllib.parse import unquote, urlparse, parse_qs

from playwright.sync_api import sync_playwright


class ChaoxingPDFDownloader:
    def __init__(self, profile_dir=None, download_dir=None, cdp_url="http://localhost:9222"):
        if profile_dir is None:
            profile_dir = os.path.join(os.getcwd(), ".chaoxing_profile")
        self.profile_dir = profile_dir
        self.cdp_url = cdp_url
        if download_dir is None:
            download_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        self.download_dir = download_dir
        os.makedirs(self.download_dir, exist_ok=True)
        self.browser = None
        self.context = None
        self.page = None
        self.downloaded_urls = set()

    def launch_browser(self, headless=False):
        os.makedirs(self.profile_dir, exist_ok=True)
        with sync_playwright() as p:
            self.context = p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                headless=headless,
                args=[
                    '--remote-debugging-port=9222',
                    '--no-first-run',
                    '--no-default-browser-check',
                ]
            )
            self.page = self.context.new_page()
            print(f"[*] 浏览器已启动")
            print(f"[*] 用户数据目录: {os.path.abspath(self.profile_dir)}")
            print(f"[*] CDP 端口: 9222")
            print("[*] 请手动登录超星学习通，登录完成后按 Ctrl+C 结束本进程\n")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n[*] 浏览器保持后台运行，下次可直接连接")

    def connect(self):
        p = sync_playwright().start()
        self.browser = p.chromium.connect_over_cdp(self.cdp_url)
        if not self.browser.contexts:
            raise RuntimeError("浏览器没有可用的 context")
        self.context = self.browser.contexts[0]

        for pg in self.context.pages:
            if "chaoxing" in pg.url and "about:blank" not in pg.url:
                self.page = pg
                break
        if not self.page:
            self.page = self.context.pages[0] if self.context.pages else None
        if not self.page:
            raise RuntimeError("找不到可用页面")

        print(f"[*] 已连接到页面: {self.page.url[:100]}")
        print(f"[*] 页面标题: {self.page.title()}")
        return self.page

    def find_all_pdfs(self):
        """扫描当前页面所有 iframe，提取可下载的文件"""
        pdfs = []
        print(f"\n[*] 正在扫描页面中的资源...")
        print(f"[*] 共 {len(self.page.frames)} 个 frames\n")

        for i, frame in enumerate(self.page.frames):
            url = frame.url
            if url == "about:blank":
                continue

            if "pan-yz.chaoxing.com" in url and "file_" in url:
                file_id = self._extract_file_id(url)
                print(f"[Frame {i}] 云盘预览页  file_id={file_id}")
                try:
                    content = frame.content()
                    links = re.findall(r'https?://[^"\'\s)]+/download/[^"\'\s)]+', content)
                    seen = set()
                    for link in links:
                        clean = link.replace("&amp;", "&")
                        if clean in seen:
                            continue
                        seen.add(clean)
                        filename = self._extract_filename_from_url(clean) or f"{file_id}.pdf"
                        pdfs.append({"type": "pan_yz", "frame": frame, "url": clean, "filename": filename})
                        print(f"  └─ 发现下载链接 -> {filename}")
                except Exception as e:
                    print(f"  └─ 获取内容失败: {e}")

            elif "/ananas/modules/pdf/index.html" in url:
                print(f"[Frame {i}] PDF Viewer")
                try:
                    href = None
                    el = frame.locator("#downloadUrl").first
                    if el.count() > 0:
                        h = el.get_attribute("href") or ""
                        if h and h != "javascript:void(0)":
                            href = h.replace("&amp;", "&")

                    if not href:
                        content = frame.content()
                        links = re.findall(r'https?://[^"\'\s)]+/download/[^"\'\s)]+', content)
                        if links:
                            href = links[0].replace("&amp;", "&")

                    # 终极备用：通过 window.data.objectid 获取
                    if not href:
                        objectid, fname = self._get_objectid_from_viewer(frame)
                        if objectid:
                            href = self._get_download_url_from_screen(objectid)
                            if href and not fname:
                                fname = f"viewer_{i}.pdf"

                    if href:
                        filename = self._extract_filename_from_url(href) or fname or f"viewer_{i}.pdf"
                        pdfs.append({"type": "viewer", "frame": frame, "url": href, "filename": filename})
                        print(f"  └─ 发现下载链接 -> {filename}")
                    else:
                        print(f"  └─ 下载按钮被禁用且未找到备用链接，已跳过")
                except Exception as e:
                    print(f"  └─ 检查失败: {e}")

        return pdfs

    def download_pdf(self, pdf_info):
        frame = pdf_info["frame"]
        url = pdf_info["url"]
        filename = pdf_info["filename"]

        if url in self.downloaded_urls:
            return True

        output_path = os.path.join(self.download_dir, filename)
        counter = 1
        base, ext = os.path.splitext(output_path)
        while os.path.exists(output_path):
            output_path = f"{base}_{counter}{ext}"
            counter += 1
        final_name = os.path.basename(output_path)

        print(f"\n[↓] 开始下载: {final_name}")
        print(f"    URL: {url[:120]}...")

        try:
            with self.page.expect_download(timeout=60000) as dl_info:
                frame.evaluate(f"""
                    () => {{
                        const a = document.createElement('a');
                        a.href = '{url}';
                        a.target = '_blank';
                        a.style.display = 'none';
                        document.body.appendChild(a);
                        a.click();
                        setTimeout(() => document.body.removeChild(a), 1000);
                    }}
                """)
            dl = dl_info.value
            dl.save_as(output_path)

            # 修正扩展名
            with open(output_path, 'rb') as f:
                header = f.read(8)
            if header.startswith(b'PK\x03\x04'):
                correct = '.xlsx' if 'xls' in final_name.lower() else '.docx'
                if not output_path.lower().endswith(correct):
                    new_path = os.path.splitext(output_path)[0] + correct
                    os.rename(output_path, new_path)
                    output_path = new_path
                    final_name = os.path.basename(new_path)

            size = os.path.getsize(output_path)
            self.downloaded_urls.add(url)
            print(f"    ✓ 成功 ({size:,} bytes)")
            return True

        except Exception as e:
            print(f"    ✗ 失败: {e}")
            return False

    def download_all(self):
        pdfs = self.find_all_pdfs()
        total = len(pdfs)
        print(f"\n[*] 共发现 {total} 个资源，开始下载...\n")

        ok = 0
        for idx, pdf in enumerate(pdfs, 1):
            print(f"[{idx}/{total}] ", end="")
            if self.download_pdf(pdf):
                ok += 1
            time.sleep(0.8)

        print(f"\n[*] 全部完成: {ok}/{total} 成功")
        if ok < total:
            print("[*] 失败的可能是签名过期，刷新课程页面后重试即可")
        return ok, total

    def bulk_download(self):
        """批量下载整门课所有章节的资源"""
        print("\n[*] 正在获取章节列表...")
        els = self.page.locator("span.posCatalog_name").all()
        chapters = []
        for i, el in enumerate(els):
            text = el.inner_text().strip().replace('\n', ' ')
            onclick = el.get_attribute("onclick") or ""
            m = re.search(r"getTeacherAjax\('(\d+)','(\d+)','(\d+)'\)", onclick)
            if m:
                chapters.append({"text": text, "knowledge_id": m.group(3), "index": i})
        print(f"[*] 共 {len(chapters)} 个章节\n")

        parsed = urlparse(self.page.url)
        qs = parse_qs(parsed.query)
        course_id = qs.get("courseId", [""])[0]
        clazz_id = qs.get("clazzid", [""])[0]
        cpi = qs.get("cpi", [""])[0]
        enc = qs.get("enc", [""])[0]
        openc = qs.get("openc", [""])[0]

        total_ok = 0
        total_fail = 0

        for ch in chapters:
            print(f"\n[{ch['index']+1}/{len(chapters)}] {ch['text'][:60]}")
            url = f"https://mooc1.chaoxing.com/mycourse/studentstudy?chapterId={ch['knowledge_id']}&courseId={course_id}&clazzid={clazz_id}&cpi={cpi}&enc={enc}&mooc2=1&hidetype=0&openc={openc}"
            try:
                self.page.goto(url, timeout=30000)
            except:
                pass
            time.sleep(5)

            pdfs = self.find_all_pdfs()
            if pdfs:
                for pdf in pdfs:
                    if self.download_pdf(pdf):
                        total_ok += 1
                    else:
                        total_fail += 1
                    time.sleep(1)
            else:
                print("    [-] 无文件")

        print(f"\n{'='*50}")
        print(f"[*] 全部完成: {total_ok} 成功, {total_fail} 失败")
        print(f"[*] 下载目录: {self.download_dir}")
        print(f"[*] 共下载 {len(self.downloaded_urls)} 个唯一文件")

    def _get_objectid_from_viewer(self, frame):
        try:
            data = frame.evaluate("() => window.data || {}")
            return data.get("objectid"), data.get("name", "")
        except:
            return None, ""

    def _get_download_url_from_screen(self, objectid):
        if not objectid:
            return None
        screen_url = f"https://mooc1.chaoxing.com/mooc-ans/screen/file?objectid={objectid}&ext=%7B%22_from_%22%3A%22259958398_139966870_445411122_a3139324498bf58fd679ea8b5042a264%22%7D"
        try:
            resp = self.page.request.get(screen_url)
            if resp.status == 200:
                links = re.findall(r'https?://[^"\'\s)]+/download/[^"\'\s)]+', resp.text())
                if links:
                    return links[0].replace("&amp;", "&")
        except:
            pass
        return None

    @staticmethod
    def _extract_file_id(url):
        m = re.search(r'file_([a-f0-9]+)', url)
        return m.group(1) if m else "unknown"

    @staticmethod
    def _extract_filename_from_url(url):
        try:
            qs = parse_qs(urlparse(url).query)
            if 'fn' in qs:
                return unquote(qs['fn'][0])
            name = urlparse(url).path.split('/')[-1]
            if '.' in name:
                return name
        except Exception:
            pass
        return None


def main():
    parser = argparse.ArgumentParser(
        description="超星学习通 PDF 批量下载器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 1. 首次使用：启动浏览器并登录
  python chaoxing_pdf_downloader.py --launch

  # 2. 下载当前页面所有资源
  python chaoxing_pdf_downloader.py --download

  # 3. 批量下载整门课所有章节
  python chaoxing_pdf_downloader.py --bulk

  # 4. 指定下载目录
  python chaoxing_pdf_downloader.py --bulk --output ./pdfs
        """
    )
    parser.add_argument("--launch", action="store_true", help="启动持久化浏览器（首次使用）")
    parser.add_argument("--download", action="store_true", help="连接浏览器并下载当前页面所有资源")
    parser.add_argument("--bulk", action="store_true", help="批量下载整门课所有章节的资源")
    parser.add_argument("--profile", default=None, help="Chrome 用户数据目录 (默认: 当前目录下的 .chaoxing_profile)")
    parser.add_argument("--output", default=None, help="保存目录 (默认: ~/Downloads)")
    parser.add_argument("--cdp", default="http://localhost:9222", help="CDP 调试地址 (默认: http://localhost:9222)")

    args = parser.parse_args()
    downloader = ChaoxingPDFDownloader(
        profile_dir=args.profile,
        download_dir=args.output,
        cdp_url=args.cdp
    )

    if args.launch:
        downloader.launch_browser()
    elif args.download:
        try:
            downloader.connect()
            downloader.download_all()
        except Exception as e:
            print(f"[!] 错误: {e}")
            print("[!] 请确认浏览器已启动且 CDP 端口 9222 可用")
            sys.exit(1)
    elif args.bulk:
        try:
            downloader.connect()
            downloader.bulk_download()
        except Exception as e:
            print(f"[!] 错误: {e}")
            print("[!] 请确认浏览器已启动且 CDP 端口 9222 可用")
            sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
