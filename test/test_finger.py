import pytest

from app.services.fingerprint_cache import finger_db_cache, finger_db_identify, have_human_rule_from_db


class DummyCursor:
    def __init__(self, items):
        self._items = list(items)

    def find(self):
        return list(self._items)

    def find_one(self, query):
        human_rule = query.get("human_rule")
        for item in self._items:
            if item.get("human_rule") == human_rule:
                return item
        return None


@pytest.fixture(autouse=True)
def stub_fingerprint_collection(monkeypatch):
    items = [
        {"name": "DemoApp", "human_rule": 'body="demo"'},
        {"name": "IconApp", "human_rule": 'icon_hash="42"'},
    ]
    cursor = DummyCursor(items)

    monkeypatch.setattr("app.services.fingerprint_cache.conn_db", lambda name: cursor)

    finger_db_cache.cache = None
    yield
    finger_db_cache.cache = None


def test_finger_db_identify_hits_cache(monkeypatch):
    calls = {"count": 0}

    original_fetch = finger_db_cache.fetch_data_from_mongodb

    def fake_fetch():
        calls["count"] += 1
        return original_fetch()

    monkeypatch.setattr(finger_db_cache, "fetch_data_from_mongodb", fake_fetch)

    variables = {
        'body': "demo",
        'header': "header",
        'title': "title",
        'icon_hash': "0",
    }

    result = finger_db_identify(variables)
    assert result == ["DemoApp"]
    # 调用第二次应复用缓存
    result = finger_db_identify(variables)
    assert result == ["DemoApp"]
    assert calls["count"] == 1


@pytest.mark.parametrize(
    "rule, expected",
    [
        ('body="demo"', True),
        ('icon_hash="42"', True),
        ('body="missing"', False),
    ],
)
def test_have_human_rule_from_db(rule, expected):
    assert have_human_rule_from_db(rule) is expected
