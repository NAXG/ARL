import pytest

from app import utils
from app.utils.fingerprint import fetch_fingerprint, parse_human_rule, transform_rule_map


def test_parse_human_rule_extracts_fields():
    human_rule = 'header="test.php" || body="test.gif" || title="test title" || icon_hash="123456"'
    rule_map = parse_human_rule(human_rule)

    assert rule_map == {
        "html": ["test.gif"],
        "title": ["test title"],
        "headers": ["test.php"],
        "favicon_hash": [123456],
    }


def test_parse_human_rule_returns_none_for_invalid_tokens():
    assert parse_human_rule("xx=fdf || fdf=xxx") is None


def test_transform_rule_map_round_trips():
    rule_map = {
        "html": ["body-token"],
        "title": ["Example"],
        "headers": ["Server: demo"],
        "favicon_hash": [42],
    }

    human_rule = transform_rule_map(rule_map)

    tokens = {token.strip() for token in human_rule.split("||")}
    assert tokens == {
        'body="body-token"',
        'title="Example"',
        'header="Server: demo"',
        'icon_hash="42"',
    }


@pytest.mark.parametrize(
    "content, headers, title, favicon_hash, expected",
    [
        (b"<html>hello demo</html>", "X-Service: none", "", 0, ["html"]),
        (b"<html>something</html>", "X-Service: demo", "demo", 0, ["header", "title"]),
        (b"irrelevant", "X-Service: none", "", 1337, ["favicon"]),
    ],
)
def test_fetch_fingerprint_matches(content, headers, title, favicon_hash, expected):
    finger_list = [
        {"name": "html", "rule": {"html": ["demo"], "headers": [], "title": [], "favicon_hash": []}},
        {"name": "header", "rule": {"html": [], "headers": ["X-Service: demo"], "title": [], "favicon_hash": []}},
        {"name": "title", "rule": {"html": [], "headers": [], "title": ["demo"], "favicon_hash": []}},
        {"name": "favicon", "rule": {"html": [], "headers": [], "title": [], "favicon_hash": [1337]}},
    ]

    result = fetch_fingerprint(
        content=content,
        headers=headers,
        title=title,
        favicon_hash=favicon_hash,
        finger_list=finger_list,
    )

    assert set(result) == set(expected)


def test_utils_get_fld_handles_subdomain():
    assert utils.get_fld("www.baidu.com") == "baidu.com"
    assert utils.get_fld("baidu.com") == "baidu.com"
