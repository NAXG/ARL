from xing.core.BasePlugin import BasePlugin
from xing.utils import http_req
from xing.core import PluginType, SchemeType


class Plugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.plugin_type = PluginType.POC
        self.vul_name = "Docker Remote API 未授权访问"
        self.app_name = 'Docker'
        self.scheme = [SchemeType.HTTPS, SchemeType.HTTP]

    def verify(self, target):
        url = target + "/version"
        conn = http_req(url)
        if b'"ApiVersion"' in conn.content and b"<" not in conn.content:
            self.logger.success(f"发现 Docker Remote API 未授权访问 {self.target}")
            return True
