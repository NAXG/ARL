import os
import re
import asyncio
from app import utils
from playwright.async_api import async_playwright

logger = utils.get_logger()


class SiteScreenshot:
    def __init__(self, sites, concurrency=10, capture_dir="./"):
        self.sites = sites
        self.concurrency = concurrency
        self.capture_dir = capture_dir
        self.screenshot_map = {}
        self.semaphore = asyncio.Semaphore(concurrency)

        # 截图配置参数 - 直接在代码中配置
        self.screenshot_config = {
            'full_page': False,  # 固定大小截图，不使用全页面（与PhantomJS一致）
            'quality': 70,  # JPEG 质量，范围 0-100，数值越大质量越高文件越大
            'viewport_width': 1280,  # 视口宽度（固定尺寸）
            'viewport_height': 1024,  # 视口高度（固定尺寸）
            'max_file_size_mb': 2,  # 最大文件大小（MB），超过则自动降低质量
            'timeout': 60000  # 截图超时时间（毫秒）
        }

    def check_file_size(self, file_path):
        """检查文件大小，如果超过限制返回True"""
        if not os.path.exists(file_path):
            return True
        file_size = os.path.getsize(file_path)
        max_size = self.screenshot_config['max_file_size_mb'] * 1024 * 1024
        return file_size > max_size

    async def work(self, site):
        """异步截图任务"""
        async with self.semaphore:
            playwright = None
            browser = None
            page = None
            file_name = f'{self.capture_dir}/{self.gen_filename(site)}.jpg'

            try:
                # 启动 Playwright 和浏览器
                playwright = await async_playwright().start()
                browser = await playwright.chromium.launch(headless=True)
                page = await browser.new_page(ignore_https_errors=True)

                # 设置视口大小（固定尺寸，与PhantomJS一致）
                viewport_width = self.screenshot_config['viewport_width']
                viewport_height = self.screenshot_config['viewport_height']
                await page.set_viewport_size({"width": viewport_width, "height": viewport_height})

                # 使用配置中的超时时间
                timeout_ms = self.screenshot_config['timeout']
                await page.goto(site, wait_until='domcontentloaded', timeout=timeout_ms)

                # 固定大小截图（非全页面）
                await page.screenshot(
                    path=file_name,
                    full_page=False,  # 固定大小截图
                    type='jpeg',
                    quality=self.screenshot_config['quality'],
                    timeout=timeout_ms
                )

                # 检查文件大小，如果超过限制则降低质量重新截图
                if self.check_file_size(file_name):
                    logger.info(f"File too large, reducing quality for {site}")
                    await page.screenshot(
                        path=file_name,
                        full_page=False,
                        type='jpeg',
                        quality=60,  # 降低质量到60
                        timeout=timeout_ms
                    )

                # 最终检查：如果文件存在且大小合理，则记录
                if os.path.exists(file_name) and not self.check_file_size(file_name):
                    self.screenshot_map[site] = file_name
                    logger.debug(f"screenshot successful for {site}")
                else:
                    logger.warning(f"screenshot too large or failed for {site}")

            except Exception as e:
                logger.warning(f"screenshot failed for {site}: {e}")
            finally:
                # 确保资源被正确释放
                if page:
                    await page.close()
                if browser:
                    await browser.close()
                if playwright:
                    await playwright.stop()

    def gen_filename(self, site):
        filename = site.replace('://', '_')
        return re.sub(r'[^\w\-_\. ]', '_', filename)

    async def run(self):
        """运行异步截图任务"""
        t1 = asyncio.get_event_loop().time()
        logger.info(f"start screen shot {len(self.sites)}")

        # 创建截图目录
        os.makedirs(self.capture_dir, 0o777, True)

        # 并发执行所有截图任务
        tasks = [self.work(site) for site in self.sites]
        await asyncio.gather(*tasks, return_exceptions=True)

        elapse = asyncio.get_event_loop().time() - t1
        logger.info(f"end screen shot elapse {elapse}")


def site_screenshot(sites, concurrency=10, capture_dir="./"):
    """同步接口，包装异步实现"""
    s = SiteScreenshot(sites, concurrency=concurrency, capture_dir=capture_dir)

    # 检查是否在事件循环中
    try:
        loop = asyncio.get_running_loop()
        # 在事件循环中，创建任务并等待
        return loop.run_until_complete(s.run())
    except RuntimeError:
        # 不在事件循环中，直接运行
        return asyncio.run(s.run())