import time
import re
from wappalyzer import analyze
from app import utils
from .baseThread import BaseThread

logger = utils.get_logger()

# 预编译正则表达式模式
VERSION_PATTERN = re.compile(r"^[\d\.\-a-zA-Z]+$")
CONFIDENCE_PATTERN = re.compile(r"^\d+$")


class WebAnalyze(BaseThread):
    __slots__ = ("analyze_map",)

    def __init__(self, sites, concurrency=3):
        super().__init__(sites, concurrency=concurrency)
        self.analyze_map = {}

    def work(self, target):
        # 使用局部变量优化频繁调用的函数（移到 try 块外避免 NameError）
        analyze_func = analyze
        logger_debug = logger.debug
        logger_warning = logger.warning

        try:
            # Use wappalyzer-next's analyze function with 'full' scan_type
            # Full scan requires Firefox browser for better detection
            # The analyze function returns a dictionary where keys are URLs
            # and values are dictionaries of detected technologies.
            results = analyze_func(url=target, threads=2, scan_type="balanced")

            # 使用推导式替代循环构建列表（PEP 709 优化）
            site_results = results.get(target, {})
            apps = (
                [
                    {
                        "name": app_name,
                        "confidence": str(
                            details.get("confidence", 0)
                        ),  # 保持类型一致：始终为 str
                        "version": str(
                            details.get("version", "")
                        ),  # 保持类型一致：始终为 str
                        "website": str(
                            details.get("website", "")
                        ),  # 保持类型一致：始终为 str
                        "categories": list(
                            details.get("categories", [])
                        ),  # 保持类型一致：始终为 list
                    }
                    for app_name, details in site_results.items()
                    if app_name and isinstance(app_name, str)  # 添加有效性检查
                ]
                if site_results
                else []
            )

            self.analyze_map[target] = apps
            logger_debug(f"WebAnalyze successful for {target}")

        except Exception as exc:
            logger_warning(f"WebAnalyze failed on {target}: {exc}")
            self.analyze_map[target] = []

    def run(self):
        t1 = time.time()
        logger.info(f"start WebAnalyze {len(self.targets)}")
        self._run()
        elapse = time.time() - t1
        logger.info(f"end WebAnalyze elapse {elapse}")
        return self.analyze_map


def web_analyze(sites, concurrency=3):
    s = WebAnalyze(sites, concurrency=concurrency)
    return s.run()
