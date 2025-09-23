import time
from app import utils
from .baseThread import BaseThread
logger = utils.get_logger()


class ProbeHTTP(BaseThread):
    def __init__(self, domains, concurrency=6):
        super().__init__(self._build_targets(domains), concurrency = concurrency)

        self.sites = []
        self.domains = domains

    def _build_targets(self, domains):
        def resolve_domain(item):
            return item.domain if hasattr(item, 'domain') else item

        return [
            f"{scheme}://{domain}"
            for item in domains
            for domain in (resolve_domain(item),)
            for scheme in ("https", "http")
        ]

    def work(self, target):
        conn = utils.http_req(target, 'get', timeout=(3, 2), stream=True)
        conn.close()

        if conn.status_code in [502, 504, 501, 422, 410]:
            logger.debug(f"{target} 状态码为 {conn.status_code} 跳过")
            return

        self.sites.append(target)

    def run(self):
        t1 = time.time()
        logger.info(f"start ProbeHTTP {len(self.targets)}")
        self._run()
        # 去除https和http相同的
        alive_site = [
            site
            for site in self.sites
            if site.startswith("https://")
            or (
                site.startswith("http://")
                and f"https://{site[7:]}" not in self.sites
            )
        ]

        elapse = time.time() - t1
        logger.info(f"end ProbeHTTP {len(alive_site)} elapse {elapse}")

        return alive_site


def probe_http(domain, concurrency=10):
    p = ProbeHTTP(domain, concurrency=concurrency)
    return p.run()
