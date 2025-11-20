import re

# 预编译正则表达式模式，提升性能
TITLE_PATTERN = re.compile(rb'<title>([^<]{1,200})</title>', re.I)


def get_title(body):
    """
    根据页面源码返回标题
    :param body: <title>sss</title>
    :return: sss
    """
    result = ''
    # 使用预编译的正则表达式模式
    title = TITLE_PATTERN.findall(body)
    if title:  # 更 Pythonic 的判断方式，避免 len() 函数调用
        try:
            result = title[0].decode("utf-8")
        except Exception:
            result = title[0].decode("gbk", errors="replace")
    return result.strip()


def get_headers(conn):
    # version 字段目前只能是10或者11

    raw = conn.raw
    version = "1.1"
    if raw.version == 10:
        version = "1.0"

    first_line = f"HTTP/{version} {raw.status} {raw.reason}\n"

    headers = str(raw._fp.headers)

    headers = headers.strip()
    if not conn.headers.get("Content-Length"):
        headers = f"{headers}\nContent-Length: {len(conn.content)}"

    return first_line + headers

