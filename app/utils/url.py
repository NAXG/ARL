import hashlib
import re
from urllib.parse import urlparse,unquote
import os
from urllib import parse

hash_size = 199999

def urlsimilar(url):
    """
        url='http://auto.sohu.com/7/0903/70/column213227075.shtml'
        first=urlsimilar(url)
        url='http://auto.sohu.com/7/4354/34/column443243545.shtml'
        second=urlsimilar(url)
        if first == second:
            print("URL similar")
        else:
            print("URL not similar")
    """
    url_parse = urlparse(url)
    netloc = url_parse.netloc
    path = url_parse.path[1:]
    if path == "":
        path = "/"
    ext = Path(path).suffix

    path = re.sub(r'\b[0-9]+\b', '0', path)
    query = unquote(url_parse.query)
    query_keys = sorted(dict(parse.parse_qsl(query)).keys())

    query_value = 0
    if len(query_keys) > 0:
        query_value = hash("-".join(query_keys)) % 98765
    if query_value:
        url_value = query_value
        return url_value

    if len(path.split('/')) > 1:
        tail = path.split('/')[-1].split('.')[-1]
    elif len(path.split('/')) == 1:
        tail = path
    else:
        tail = '1'

    path_length = len(path.split('/')) - 1

    path_list = path.split('/')[:-1] + [tail]
    path_value = 0
    for i in range(path_length + 1):
        if path_length - i == 0:
            path_value += hash(path_list[path_length - i]) % 98765
        else:
            path_value += len(path_list[path_length - i]) * (10 ** (i + 1))
    path_value += hash(ext)

    # scheme_hash = hashlib.md5()
    # scheme_hash.update(scheme.encode('utf-8'))
    # scheme_value = hash(scheme_hash.hexdigest()) % hash_size

    netloc_hash = hashlib.md5()
    netloc_hash.update(netloc.encode('utf-8'))
    netloc_value = hash(netloc_hash.hexdigest()) % hash_size

    url_hash = hashlib.md5()
    url_hash.update(netloc.encode('utf-8'))

    url_hash.update(str(path_value + netloc_value).encode('utf-8'))
    url_value = hash(url_hash.hexdigest()) % hash_size
    return url_value


def get_hostname(url):
    if "://" not in url:
        url = "http://" + url
    return urlparse(url).netloc


def rm_similar_url(all_url):
    # URL简单去似
    seen_values = set()
    filther_similar_url = [
        filtered_url
        for raw_url in all_url
        if (filtered_url := normal_url(raw_url))
        and (url_value := urlsimilar(filtered_url)) not in seen_values
        and not seen_values.add(url_value)
    ]
    return filther_similar_url


def normal_url(url):
    scheme_map = {
        'http': 80,
        "https": 443
    }
    o = urlparse(url)

    scheme = o.scheme
    hostname = o.hostname
    path = o.path

    if scheme not in scheme_map:
        return

    if o.path == "":
        path = "/"

    if o.port == scheme_map[o.scheme] or o.port is None:
        ret_url = f"{scheme}://{hostname}{path}"

    else:
        ret_url = f"{scheme}://{hostname}:{o.port}{path}"

    if o.query:
        ret_url = ret_url + "?" + o.query

    return ret_url


def cut_filename(url):
    o = urlparse(url)
    dir_path = os.path.dirname(o.path)
    dir_path = dir_path.rstrip("/")
    if not o.netloc:
        return ""
    ret_url = f"{o.scheme}://{o.netloc}{dir_path}"
    return ret_url


def same_netloc(url1, url2):
    h1 = get_hostname(url1)
    h2 = get_hostname(url2)
    return h1 == h2


def verify_cert(url):
    from . import http_req
    try:
        http_req(url, method='head', verify= True)
        return True
    except Exception:
        return False


def url_ext(url):
    url_parse = urlparse(url)
    path = url_parse.path
    ext = Path(path).suffix
    return ext.lower()
