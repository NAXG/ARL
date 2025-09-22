from xing.core.BasePlugin import BasePlugin
from xing.utils import http_req
from xing.core import PluginType, SchemeType


class Plugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.plugin_type = PluginType.POC
        self.vul_name = "发现 Harbor API"
        self.app_name = 'Harbor'
        self.scheme = [SchemeType.HTTP, SchemeType.HTTPS]

    def verify(self, target):
        paths = ["/api/systeminfo", "/harbor/api/systeminfo"]
        for path in paths:
            url = target + path
            conn = http_req(url)

            if conn.status_code != 200:
                continue

            if b'"harbor_version"' in conn.content and b"<" not in conn.content:
                self.logger.success(f"found {self.app_name} {url}")
                return url

