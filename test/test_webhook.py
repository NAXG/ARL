from types import SimpleNamespace

from app.services.webhook import domain_asset_web_hook, ip_asset_web_hook


class DummyCollection:
    def __init__(self, items=None, one=None):
        self._items = items or []
        self._one = one

    def find(self, query, projection=None):
        return DummyCursor(self._items)

    def find_one(self, query, projection=None):
        return dict(self._one) if self._one else None


class DummyCursor:
    def __init__(self, items):
        self._items = items

    def limit(self, _):
        return self

    def __iter__(self):
        return iter(self._items)


def stub_conn_db(data_map):
    def factory(name):
        return data_map[name]
    return factory


def test_domain_asset_web_hook_sends_payload(monkeypatch):
    data_map = {
        "domain": DummyCollection(items=[{"domain": "a"}]),
        "site": DummyCollection(items=[{"site": "https://a"}]),
        "asset_scope": DummyCollection(one={"_id": "0" * 24, "name": "scope", "scope_type": "domain"}),
        "task": DummyCollection(one={"_id": "0" * 24, "name": "task"}),
    }

    sent = {}
    monkeypatch.setattr("app.services.webhook.Config.WEB_HOOK_URL", "https://hook")
    monkeypatch.setattr("app.services.webhook.Config.WEB_HOOK_TOKEN", "token")
    monkeypatch.setattr("app.services.webhook.utils.conn_db", stub_conn_db(data_map))
    monkeypatch.setattr("app.services.webhook.utils.http_req", lambda url, **kwargs: sent.update({"url": url, **kwargs}))

    domain_asset_web_hook("0" * 24, "1" * 24)

    assert sent["url"] == "https://hook"
    assert sent["headers"]["Token"] == "token"
    assert sent["json"]["type"] == "domain_monitor"


def test_ip_asset_web_hook_requires_assets(monkeypatch):
    data_map = {
        "ip": DummyCollection(items=[]),
        "site": DummyCollection(items=[]),
        "asset_scope": DummyCollection(one={"_id": "0" * 24}),
        "task": DummyCollection(one={"_id": "0" * 24}),
    }
    monkeypatch.setattr("app.services.webhook.Config.WEB_HOOK_URL", "https://hook")
    monkeypatch.setattr("app.services.webhook.Config.WEB_HOOK_TOKEN", "token")
    monkeypatch.setattr("app.services.webhook.utils.conn_db", stub_conn_db(data_map))

    called = {}
    monkeypatch.setattr("app.services.webhook.utils.http_req", lambda *args, **kwargs: called.update({"called": True}))

    ip_asset_web_hook("0" * 24, "1" * 24)

    assert called == {}
