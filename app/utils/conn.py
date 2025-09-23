import urllib3
import requests
from app.config import Config
from pymongo import MongoClient

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


UA = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"


proxies = {
    'https': "http://127.0.0.1:8080",
    'http': "http://127.0.0.1:8080"
}

SET_PROXY = False


def http_req(url, method='get', **kwargs):
    kwargs.setdefault('verify', False)
    kwargs.setdefault('timeout', (10.1, 30.1))
    kwargs.setdefault('allow_redirects', False)
    kwargs.setdefault('stream', False)

    headers = kwargs.get("headers", {})
    headers.setdefault("User-Agent", UA)
    # 不允许缓存
    headers.setdefault("Cache-Control", "max-age=0")

    kwargs["headers"] = headers
    kwargs["stream"] = True

    if Config.PROXY_URL:
        proxies['https'] = Config.PROXY_URL
        proxies['http'] = Config.PROXY_URL
        kwargs["proxies"] = proxies

    conn = getattr(requests, method)(url, **kwargs)
    if not kwargs.get('stream'):
        # 触发内容加载，让 requests 自行处理缓存
        _ = conn.content

    return conn


class ConnMongo:
    def __new__(self):
        if not hasattr(self, 'instance'):
            self.instance = super().__new__(self)
            self.instance.conn = MongoClient(Config.MONGO_URL)
        return self.instance


def conn_db(collection, db_name = None):
    conn = ConnMongo().conn
    if db_name:
        return conn[db_name][collection]

    else:
        return conn[Config.MONGO_DB][collection]
