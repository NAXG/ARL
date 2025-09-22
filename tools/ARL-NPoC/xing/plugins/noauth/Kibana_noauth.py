from xing.core.BasePlugin import BasePlugin
from xing.utils import http_req
from xing.core import PluginType, SchemeType


class Plugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.plugin_type = PluginType.POC
        self.vul_name = "Kibana 未授权访问"
        self.app_name = 'Kibana'
        self.scheme = [SchemeType.HTTPS, SchemeType.HTTP]

    def verify(self, target):
        url = target + "/app/kibana"
        conn = http_req(url)
        if b'.kibanaWelcomeView' in conn.content:
            self.logger.success(f"发现 Kibana 未授权访问 {self.target}")
            return True
