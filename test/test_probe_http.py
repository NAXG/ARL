
from app.services import check_http, probe_http


class DummyResponse:
    def __init__(self, status_code, headers=None, content=b"", text=""):
        self.status_code = status_code
        self.headers = headers or {}
        self.content = content
        self.text = text or content.decode(errors="ignore")

    def close(self):
        pass


def test_probe_http_prefers_https(monkeypatch):
    monkeypatch.setattr(
        "app.services.probeHTTP.BaseThread._run",
        lambda self: [self.work(target) for target in self.targets],
    )

    def fake_http_req(target, method="get", timeout=None, stream=False):
        return DummyResponse(200)

    monkeypatch.setattr("app.services.probeHTTP.utils.http_req", fake_http_req)

    results = probe_http(["demo.com"])

    assert results == ["https://demo.com"]


def test_check_http_returns_status_map(monkeypatch):
    monkeypatch.setattr(
        "app.services.checkHTTP.BaseThread._run",
        lambda self: [self.work(target) for target in self.targets],
    )

    def fake_http_req(url, method="get", timeout=None, stream=False):
        headers = {"Content-Type": "text/html"}
        return DummyResponse(200, headers=headers, content=b"<html></html>")

    monkeypatch.setattr("app.services.checkHTTP.utils.http_req", fake_http_req)

    result = check_http(["http://demo.com"])

    assert result == {"http://demo.com": {"status": 200, "content-type": "text/html"}}
