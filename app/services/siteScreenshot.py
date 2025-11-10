import os
import re
import time
from app import utils
from .baseThread import BaseThread
from playwright.sync_api import sync_playwright

logger = utils.get_logger()


class SiteScreenshot(BaseThread):
    def __init__(self, sites, concurrency=3, capture_dir="./"):
        super().__init__(sites, concurrency=concurrency)
        self.capture_dir = capture_dir
        self.screenshot_map = {}
        # 延迟启动 Playwright 和浏览器，避免资源过早占用

    def work(self, site):
        file_name = f'{self.capture_dir}/{self.gen_filename(site)}.jpg'
        page = None
        try:
            page = self.browser.new_page(ignore_https_errors=True)
            page.goto(site, wait_until='domcontentloaded', timeout=60000)
            page.screenshot(path=file_name, full_page=True, timeout=60000)
            self.screenshot_map[site] = file_name
            logger.debug(f"screenshot successful for {site}")
        except Exception as e:
            logger.warning(f"screenshot failed for {site}: {e}")
        finally:
            if page:
                page.close()

    def gen_filename(self, site):
        filename = site.replace('://', '_')
        return re.sub(r'[^\w\-_\. ]', '_', filename)

    def run(self):
        t1 = time.time()
        logger.info(f"start screen shot {len(self.targets)}")

        # 在 run() 中启动资源，确保能正确关闭
        # Use Chromium for faster screenshot (more performant)
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        os.makedirs(self.capture_dir, 0o777, True)

        try:
            self._run()
        finally:
            # 确保资源被正确释放
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()

        elapse = time.time() - t1
        logger.info(f"end screen shot elapse {elapse}")


def site_screenshot(sites, concurrency = 3, capture_dir="./"):
    s = SiteScreenshot(sites, concurrency = concurrency, capture_dir = capture_dir)
    s.run()