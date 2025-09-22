import unittest
from app.config import Config
from app.utils import http_req, get_logger, get_title

logger = get_logger()


class TestProxyURL(unittest.TestCase):
    def test_proxy_url(self):
        self.assertTrue(Config.PROXY_URL)
        target = "https://www.baidu.com"
        conn = http_req(target)
        code = conn.status_code
        logger.info(f"req:{target} proxy:{Config.PROXY_URL}")
        title = get_title(conn.content)
        logger.info(f"status_code:{code} title:{title} body_length:{len(conn.content)}")

        self.assertTrue(conn.status_code == 200)


if __name__ == '__main__':
    unittest.main()
