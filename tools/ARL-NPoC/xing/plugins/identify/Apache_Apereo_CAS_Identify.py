from xing.core.BasePlugin import BasePlugin
from xing.utils import http_req
from xing.core import PluginType, SchemeType


class Plugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.plugin_type = PluginType.POC
        self.vul_name = "发现 Apache Apereo Cas"
        self.app_name = 'Apache Apereo'
        self.scheme = [SchemeType.HTTP, SchemeType.HTTPS]

    def verify(self, target):
        path_list = ["/cas/login"]
        check = b"Apereo"
        for path in path_list:
            url = target + path
            conn = http_req(url)
            if check in conn.content and b'cas' in conn.content:
                self.logger.success(f"found {self.app_name} {url}")
                return url
