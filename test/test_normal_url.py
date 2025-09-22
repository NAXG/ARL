from app.utils import normal_url


def test_normal_url_removes_default_port():
    assert normal_url("https://www.baidu.com:443/test?a=1") == "https://www.baidu.com/test?a=1"

