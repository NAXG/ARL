import mmh3
import pytest

from app.services.fetchSite import FetchFavicon


def test_fetch_favicon_falls_back_to_html_icon(monkeypatch):
    raw_bytes = b"\x00ICO" * 40
    expected_data = FetchFavicon("https://fallback.local").encode_bas64_lines(raw_bytes)
    expected_hash = mmh3.hash(expected_data)

    class DummyResponse:
        def __init__(self, content, status_code, headers=None):
            self.content = content
            self.status_code = status_code
            self.headers = headers or {}

    def fake_http_req(url, allow_redirects=True):
        if url.endswith("favicon.ico"):
            return DummyResponse(b"short", 200, {"Content-Type": "image/png"})
        if url.endswith("/icon.ico"):
            return DummyResponse(raw_bytes, 200, {"Content-Type": "image/x-icon"})
        if url == "https://fallback.local":
            html = "<html><head><link rel=\"icon\" href=\"/icon.ico\" /></head></html>"
            return DummyResponse(html.encode(), 200, {"Content-Type": "text/html"})
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr("app.services.fetchSite.http_req", fake_http_req)

    favicon = FetchFavicon("https://fallback.local")
    result = favicon.run()

    assert result == {
        "data": expected_data,
        "url": "https://fallback.local/icon.ico",
        "hash": expected_hash,
    }
