import pytest

from app.modules import SiteAutoTag
from app.services.autoTag import auto_tag


@pytest.mark.parametrize(
    "item, expected",
    [
        (
            {
                "site": "https://foo.com",
                "hostname": "foo.com",
                "title": "Welcome to nginx",
                "status": 200,
                "headers": "Content-Type: text/html",
                "body_length": 1200,
            },
            SiteAutoTag.INVALID,
        ),
        (
            {
                "site": "https://foo.com",
                "hostname": "foo.com",
                "title": "",
                "status": 302,
                "headers": "Connection: keep-alive\nLocation: https://foo.com/login",
                "body_length": 80,
            },
            SiteAutoTag.INVALID,
        ),
        (
            {
                "site": "https://foo.com",
                "hostname": "foo.com",
                "title": "",
                "status": 302,
                "headers": "Connection: close\nLocation: https://bar.com/welcome",
                "body_length": 80,
            },
            SiteAutoTag.ENTRY,
        ),
        (
            {
                "site": "https://foo.com",
                "hostname": "foo.com",
                "title": "",
                "status": 200,
                "headers": "Content-Type: text/html",
                "body_length": 100,
            },
            SiteAutoTag.INVALID,
        ),
        (
            {
                "site": "https://foo.com",
                "hostname": "foo.com",
                "title": "",
                "status": 200,
                "headers": "Content-Type: text/html",
                "body_length": 320,
            },
            SiteAutoTag.ENTRY,
        ),
    ],
)
def test_auto_tag_dict_input(item, expected):
    auto_tag(item)
    assert item["tag"] == [expected]


def test_auto_tag_accepts_list_input():
    items = [
        {
            "site": "https://inside.local",
            "hostname": "inside.local",
            "title": "Error 404--Not Found",
            "status": 404,
            "headers": "Content-Type: text/html",
            "body_length": 1024,
        },
        {
            "site": "https://inside.local/welcome",
            "hostname": "inside.local",
            "title": "",
            "status": 200,
            "headers": "Content-Type: text/html",
            "body_length": 600,
        },
    ]

    auto_tag(items)

    assert items[0]["tag"] == [SiteAutoTag.INVALID]
    assert items[1]["tag"] == [SiteAutoTag.ENTRY]
