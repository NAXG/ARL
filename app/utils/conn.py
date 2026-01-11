import urllib3
import requests
from app.config import Config
from pymongo import MongoClient

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


UA = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"


def http_req(url, method="get", **kwargs):
    kwargs.setdefault("verify", False)
    kwargs.setdefault("timeout", (10.1, 30.1))
    kwargs.setdefault("allow_redirects", False)
    stream = kwargs.setdefault("stream", False)

    headers = kwargs.get("headers", {})
    headers.setdefault("User-Agent", UA)
    # 不允许缓存
    headers.setdefault("Cache-Control", "max-age=0")
    kwargs["headers"] = headers

    if Config.PROXY_URL:
        kwargs["proxies"] = {"https": Config.PROXY_URL, "http": Config.PROXY_URL}

    conn = getattr(requests, method)(url, **kwargs)
    if not stream:
        # 非流式模式：触发内容加载，确保连接被正确释放
        _ = conn.content

    return conn


class ConnMongo:
    instance: "ConnMongo"
    conn: MongoClient

    def __new__(cls):
        if not hasattr(cls, "instance"):
            cls.instance = super().__new__(cls)
            cls.instance.conn = MongoClient(Config.MONGO_URL)
        return cls.instance


def conn_db(collection, db_name=None):
    conn = ConnMongo().conn
    if db_name:
        return conn[db_name][collection]

    else:
        return conn[Config.MONGO_DB][collection]
