from types import SimpleNamespace

from app.utils.conn import http_req


def test_http_req_uses_configured_proxy(monkeypatch):
    captured = {}

    monkeypatch.setattr("app.config.Config.PROXY_URL", "http://proxy:8080")
    monkeypatch.setattr("app.utils.conn.proxies", {"https": "", "http": ""})

    def fake_get(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return SimpleNamespace(content=b"", status_code=200, raw=None)

    monkeypatch.setattr("app.utils.conn.requests.get", fake_get)

    conn = http_req("https://example.com")

    assert conn.status_code == 200
    assert captured["url"] == "https://example.com"
    assert captured["kwargs"]["proxies"] == {
        "https": "http://proxy:8080",
        "http": "http://proxy:8080",
    }
    assert captured["kwargs"]["headers"]["User-Agent"]
