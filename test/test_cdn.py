import pytest

from app.utils import get_cdn_name_by_cname, get_cdn_name_by_ip


@pytest.mark.parametrize(
    "ip, expected",
    [
        ("1.1.1.1", ""),
        ("164.88.98.2", "云盾CDN"),
    ],
)
def test_get_cdn_name_by_ip(ip, expected):
    assert get_cdn_name_by_ip(ip) == expected


@pytest.mark.parametrize(
    "cname, expected",
    [
        ("example.com", ""),
        ("zff.qaxwzws.com", "网神CDN"),
        ("zff.xxgslb.com", "CDN"),
        ("zff.akamaized.net", "AkamaiCDN"),
    ],
)
def test_get_cdn_name_by_cname(cname, expected):
    assert get_cdn_name_by_cname(cname) == expected
