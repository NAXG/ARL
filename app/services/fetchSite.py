import time
from pyquery import PyQuery as pq
import binascii
from urllib.parse import urljoin, urlparse
import mmh3
import requests
from app import utils
from .baseThread import BaseThread
from .autoTag import auto_tag
from app.utils import http_req, normal_url
from app.utils.fingerprint import load_fingerprint, fetch_fingerprint

logger = utils.get_logger()


class FetchSite(BaseThread):
    __slots__ = ("site_info_list", "fingerprint_list", "http_timeout")

    def __init__(self, sites, concurrency=6, http_timeout=None):
        super().__init__(sites, concurrency)
        self.site_info_list = []
        self.fingerprint_list = load_fingerprint()
        # 保持类型一致：http_timeout 始终为 tuple
        if http_timeout is None:
            self.http_timeout = (10.1, 30.1)
        elif isinstance(http_timeout, (int, float)):
            self.http_timeout = (float(http_timeout), float(http_timeout) * 3)
        elif isinstance(http_timeout, (list, tuple)) and len(http_timeout) == 2:
            self.http_timeout = (float(http_timeout[0]), float(http_timeout[1]))
        else:
            self.http_timeout = (10.1, 30.1)

    def fetch_fingerprint(self, item, content):
        favicon = item.get("favicon") or {}
        favicon_hash_raw = favicon.get("hash", 0)
        favicon_hash = str(favicon_hash_raw)

        result = fetch_fingerprint(
            content=content,
            headers=item["headers"],
            title=item["title"],
            favicon_hash=favicon_hash,
            finger_list=self.fingerprint_list,
        )

        result_db = finger_identify(
            content=content,
            header=item["headers"],
            title=item["title"],
            favicon_hash=favicon_hash,
        )  # 使用一致的 str 类型

        result = set(result + result_db)

        # 使用推导式替代循环（PEP 709 优化）
        finger = [
            {
                "icon": "default.png",
                "name": str(name),  # 保持类型一致：始终为 str
                "confidence": "80",  # 保持类型一致：始终为 str
                "version": "",  # 保持类型一致：始终为 str
                "website": "https://www.riskivy.com",  # 保持类型一致：始终为 str
                "categories": [],  # 保持类型一致：始终为 list
            }
            for name in result
            if name and isinstance(name, str)  # 确保数据有效性
        ]

        if finger:
            item["finger"] = finger

    def work(self, target, max_redirect=5):
        if max_redirect <= 0:
            return

        parsed = urlparse(target)
        hostname = parsed.hostname or ""

        conn = utils.http_req(target, timeout=self.http_timeout)
        item = {
            "site": target[:200],
            "hostname": hostname,
            "ip": "",
            "title": utils.get_title(conn.content),
            "status": conn.status_code,
            "headers": utils.get_headers(conn),
            "http_server": conn.headers.get("Server", ""),
            "body_length": len(conn.content),
            "finger": [],
            "favicon": fetch_favicon(target),
        }

        self.fetch_fingerprint(item, content=conn.content)
        domain_parsed = utils.domain_parsed(hostname)
        if domain_parsed:
            item["fld"] = domain_parsed["fld"]
            ips = utils.get_ip(hostname)
            if ips:
                item["ip"] = ips[0]
        else:
            item["ip"] = hostname

        # 保存站点信息
        if (
            max_redirect == 5
            or max_redirect == 1
            or (conn.status_code != 301 and conn.status_code != 302)
        ):
            self.site_info_list.append(item)

        if conn.status_code == 301 or conn.status_code == 302:
            url_302 = urljoin(target, conn.headers.get("Location", ""))
            url_302 = normal_url(url_302)

            # 防御性编程，防止url过长
            if len(url_302) > 260:
                return

            if url_302 != target and same_netloc_and_scheme(url_302, target):
                self.work(url_302, max_redirect=max_redirect - 1)

    def run(self):
        t1 = time.time()
        logger.info(f"start fetch site {len(self.targets)}")
        self._run()
        elapse = time.time() - t1
        logger.info(f"end fetch site elapse {elapse}")

        # 对站点信息自动打标签
        auto_tag(self.site_info_list)

        return self.site_info_list


def finger_identify(content: bytes, header: str, title: str, favicon_hash: str):
    from app.services import finger_db_identify

    try:
        content = content.decode("utf-8")
    except UnicodeDecodeError:
        content = content.decode("gbk", "ignore")

    variables = {
        "body": content,
        "header": header,
        "title": title,
        "icon_hash": favicon_hash,
    }

    return finger_db_identify(variables)


def same_netloc_and_scheme(u1, u2):
    u1 = normal_url(u1)
    u2 = normal_url(u2)
    parsed1 = urlparse(u1)
    parsed2 = urlparse(u2)

    if parsed1.scheme == parsed2.scheme and parsed1.netloc == parsed2.netloc:
        return True

    return False


def fetch_favicon(url):
    f = FetchFavicon(url)
    return f.run()


def fetch_site(sites, concurrency=15, http_timeout=None):
    # 更新数据库缓存
    from app.services import finger_db_cache

    finger_db_cache.update_cache()

    f = FetchSite(sites, concurrency=concurrency, http_timeout=http_timeout)
    return f.run()


class FetchFavicon:
    def __init__(self, url):
        self.url = url
        self.favicon_url = None
        pass

    def build_result(self, data, hash_value):
        result = {"data": data, "url": self.favicon_url, "hash": hash_value}
        return result

    def run(self):
        result = {}
        try:
            favicon_url = urljoin(self.url, "/favicon.ico")
            data = self.get_favicon_data(favicon_url)
            if data:
                self.favicon_url = favicon_url
                b64_data, hash_value = data
                return self.build_result(b64_data, hash_value)

            favicon_url = self.find_icon_url_from_html()
            if not favicon_url:
                return result
            data = self.get_favicon_data(favicon_url)
            if data:
                self.favicon_url = favicon_url
                b64_data, hash_value = data
                return self.build_result(b64_data, hash_value)

        except requests.exceptions.RequestException:
            logger.info(f"favicon request failed on {self.url}")
        except Exception as e:
            logger.warning(f"error on {self.url} {e}")

        return result

    def get_favicon_data(self, favicon_url):
        conn = http_req(favicon_url, allow_redirects=True)
        if conn.status_code != 200:
            return

        if len(conn.content) <= 80:
            logger.debug("favicon content len lt 100")
            return

        if "image" in conn.headers.get("Content-Type", ""):
            # 维持与主干一致的多行 Base64 形式，保证 Shodan hash 兼容
            b64_data = self.encode_bas64_lines(conn.content)
            hash_value = mmh3.hash(b64_data)
            return b64_data, hash_value

    def encode_bas64_lines(self, s):
        """Encode bytes into multiple lines of base-64 data (76 字符换行)."""
        max_line_size = 76  # exclude CRLF
        max_bin_size = (max_line_size // 4) * 3
        pieces = []
        for i in range(0, len(s), max_bin_size):
            chunk = s[i : i + max_bin_size]
            pieces.append(binascii.b2a_base64(chunk).decode())
        return "".join(pieces)

    def find_icon_url_from_html(self):
        conn = http_req(self.url, allow_redirects=True)
        if b"<link" not in conn.content:
            return
        d = pq(conn.content)
        links = d("link").items()
        icon_link_list = []
        for link in links:
            if link.attr("href") and "icon" in (link.attr("rel") or ""):
                icon_link_list.append(link)

        for link in icon_link_list:
            if "shortcut" in link:
                return urljoin(self.url, link.attr("href"))

        if icon_link_list:
            return urljoin(self.url, icon_link_list[0].attr("href"))
