import os
import re
import asyncio
from app import utils
from playwright.async_api import async_playwright

logger = utils.get_logger()

# 浏览器启动参数常量（避免重复）
BROWSER_ARGS = [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-dev-shm-usage',
    '--disable-gpu'
]


class BrowserPool:
    """浏览器池管理器 - 复用浏览器实例以提升性能"""

    def __init__(self, pool_size=5):
        self.pool_size = pool_size
        self.browsers = []
        self.playwright = None
        self.lock = asyncio.Lock()

    async def initialize(self):
        """初始化浏览器池"""
        async with self.lock:
            if self.playwright is None:
                self.playwright = await async_playwright().start()
                # 预创建浏览器实例
                for _ in range(self.pool_size):
                    browser = await self.playwright.chromium.launch(
                        headless=True,
                        args=BROWSER_ARGS
                    )
                    self.browsers.append(browser)

    async def acquire(self):
        """从池中获取一个浏览器实例"""
        async with self.lock:
            if not self.browsers:
                # 如果池为空，创建新的浏览器实例
                return await self.playwright.chromium.launch(
                    headless=True,
                    args=BROWSER_ARGS
                )
            return self.browsers.pop()

    async def release(self, browser):
        """归还浏览器实例到池中"""
        async with self.lock:
            if len(self.browsers) < self.pool_size:
                # 重置浏览器状态以便重用
                try:
                    contexts = browser.contexts
                    for context in contexts:
                        await context.close()
                except:
                    pass
                self.browsers.append(browser)

    async def close(self):
        """关闭所有浏览器实例"""
        async with self.lock:
            for browser in self.browsers:
                try:
                    await browser.close()
                except:
                    pass
            self.browsers.clear()

            if self.playwright:
                await self.playwright.stop()
                self.playwright = None


class SiteScreenshot:
    def __init__(self, sites, concurrency=6, capture_dir="./", pool_size=3):
        self.sites = sites
        self.concurrency = concurrency
        self.capture_dir = capture_dir
        self.screenshot_map = {}
        self.semaphore = asyncio.Semaphore(concurrency)
        self.pool_size = min(pool_size, concurrency)  # 池大小不超过并发数
        self.browser_pool = BrowserPool(pool_size=self.pool_size)

        # 截图配置参数 - 直接在代码中配置
        self.screenshot_config = {
            'full_page': False,  # 固定大小截图，不使用全页面（与PhantomJS一致）
            'quality': 60,  # JPEG 质量，范围 0-100，数值越大质量越高文件越大（默认60节省空间）
            'viewport_width': 1280,  # 视口宽度（固定尺寸）
            'viewport_height': 1024,  # 视口高度（固定尺寸）
            'timeout': 40000  # 截图超时时间（毫秒）- 40秒
        }

    async def work(self, site):
        """异步截图任务 - 使用浏览器池复用实例"""
        async with self.semaphore:
            browser = None
            page = None
            file_name = f'{self.capture_dir}/{self.gen_filename(site)}.jpg'

            try:
                # 从池中获取浏览器实例
                browser = await self.browser_pool.acquire()

                # 创建新页面
                page = await browser.new_page(
                    ignore_https_errors=True,
                    java_script_enabled=True
                )

                # 设置视口大小（直接使用配置值）
                await page.set_viewport_size({
                    "width": self.screenshot_config['viewport_width'],
                    "height": self.screenshot_config['viewport_height']
                })

                # 设置用户代理，避免被反爬
                await page.set_extra_http_headers({
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                })

                # 直接执行截图（DOM完成+50ms等待后立即截图）
                await self._screenshot_with_load(page, file_name, site)

                # 最终检查：如果文件存在则记录（默认质量60一般不会超过2MB限制）
                if os.path.exists(file_name):
                    self.screenshot_map[site] = file_name
                    logger.debug(f"screenshot successful for {site}")
                else:
                    logger.warning(f"screenshot failed for {site}")

            except Exception as e:
                logger.warning(f"screenshot failed for {site}: {e}")
            finally:
                # 确保资源被正确释放
                if page:
                    try:
                        await page.close()
                    except:
                        pass
                if browser:
                    # 归还浏览器到池中，而不是关闭
                    await self.browser_pool.release(browser)

    async def _screenshot_with_load(self, page, file_name, site):
        """内部方法：等待DOM完成后立即截图"""
        try:
            # 等待DOM内容加载完成，然后立即截图
            await page.goto(site, wait_until='domcontentloaded', timeout=2500)

            # DOM解析完成后立即截图，不额外等待
            # 确保页面基本的JavaScript执行完成
            await asyncio.sleep(0.05)  # 仅等待50ms确保JS开始执行
        except Exception as e:
            logger.debug(f"DOM load timeout for {site}, force screenshot: {e}")

        # DOM完成或超时后立即截图
        await self._take_screenshot(page, file_name)

    def _take_screenshot(self, page, file_name, quality=None):
        """内部方法：执行截图操作（避免重复代码）"""
        screenshot_config = self.screenshot_config
        return page.screenshot(
            path=file_name,
            full_page=screenshot_config['full_page'],
            type='jpeg',
            quality=quality if quality is not None else screenshot_config['quality'],
            timeout=5000  # 截图操作超时
        )

    def gen_filename(self, site):
        filename = site.replace('://', '_')
        return re.sub(r'[^\w\-_\. ]', '_', filename)

    async def run(self):
        """运行异步截图任务"""
        t1 = asyncio.get_event_loop().time()
        logger.info(f"start screen shot {len(self.sites)} (pool_size={self.pool_size}, concurrency={self.concurrency})")

        # 创建截图目录
        os.makedirs(self.capture_dir, 0o777, True)

        # 初始化浏览器池
        await self.browser_pool.initialize()
        logger.info(f"Browser pool initialized with {self.pool_size} instances")

        try:
            # 并发执行所有截图任务
            tasks = [self.work(site) for site in self.sites]
            await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            # 确保浏览器池被正确关闭
            await self.browser_pool.close()
            logger.info("Browser pool closed")

        elapse = asyncio.get_event_loop().time() - t1
        logger.info(f"end screen shot elapse {elapse}")


def site_screenshot(sites, concurrency=3, capture_dir="./", pool_size=1):
    """同步接口，包装异步实现
    Args:
        sites: 要截图的站点列表
        concurrency: 并发数
        capture_dir: 截图保存目录
        pool_size: 浏览器池大小（默认5，建议不超过并发数）
    """
    s = SiteScreenshot(sites, concurrency=concurrency, capture_dir=capture_dir, pool_size=pool_size)

    # 检查是否在事件循环中
    try:
        loop = asyncio.get_running_loop()
        # 在事件循环中，创建任务并等待
        return loop.run_until_complete(s.run())
    except RuntimeError:
        # 不在事件循环中，直接运行
        return asyncio.run(s.run())