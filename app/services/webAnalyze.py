import time
from wappalyzer import analyze
from app import utils
from .baseThread import BaseThread

logger = utils.get_logger()


class WebAnalyze(BaseThread):
    def __init__(self, sites, concurrency=3):
        super().__init__(sites, concurrency=concurrency)
        self.analyze_map = {}

    def work(self, site):
        try:
            # Use wappalyzer-next's analyze function with 'full' scan_type
            # Full scan requires Firefox browser for better detection
            # The analyze function returns a dictionary where keys are URLs
            # and values are dictionaries of detected technologies.
            results = analyze(url=site)

            apps = []
            # The result format is {url: {app_name: {version, confidence, categories, website}}}
            # We need to extract the applications list in the format expected by the original code.
            site_results = results.get(site, {})
            if site_results:
                for app_name, details in site_results.items():
                    apps.append({
                        "name": app_name,
                        "confidence": str(details.get('confidence', 0)),  # Convert to string as original code expects string
                        "version": details.get('version', ''),
                        "website": details.get('website', ''),  # wappalyzer-next provides website per app
                        "categories": details.get('categories', [])
                    })

            self.analyze_map[site] = apps
            logger.debug(f"WebAnalyze successful for {site}")

        except Exception as exc:
            logger.warning(f"WebAnalyze failed on {site}: {exc}")
            self.analyze_map[site] = []

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




