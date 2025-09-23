import base64

import mmh3

from app.services.fetchSite import FetchFavicon, same_netloc_and_scheme


def test_same_netloc_and_scheme():
    assert same_netloc_and_scheme("https://example.com/path", "https://example.com/foo")
    assert not same_netloc_and_scheme("https://example.com", "http://example.com")
    assert not same_netloc_and_scheme("https://example.com", "https://example.org")


def test_encode_bas64_lines_wraps_output():
    favicon = FetchFavicon("https://example.com")
    data = b"A" * 256
    encoded = favicon.encode_bas64_lines(data)

    for line in encoded.splitlines():
        assert len(line) <= 76

    # 确保与标准 Base64 解码保持一致
    decoded = base64.b64decode(encoded)
    assert decoded == data


def test_fetch_favicon_prefers_direct_icon(monkeypatch):
    raw_bytes = b"\x89PNG" * 40
    expected_data = FetchFavicon("https://example.com").encode_bas64_lines(raw_bytes)
    expected_hash = mmh3.hash(expected_data)

    class DummyResponse:
        def __init__(self, content, status_code, headers=None):
            self.content = content
            self.status_code = status_code
            self.headers = headers or {"Content-Type": "image/png"}

    def fake_http_req(url, allow_redirects=True):
        assert url in {"https://example.com", "https://example.com/favicon.ico"}
        if url.endswith("favicon.ico"):
            return DummyResponse(raw_bytes, 200)
        html = b"<html><head><link rel=\"icon\" href=\"/other.ico\" /></head></html>"
        return DummyResponse(html, 200, {"Content-Type": "text/html"})

    monkeypatch.setattr("app.services.fetchSite.http_req", fake_http_req)

    favicon = FetchFavicon("https://example.com")
    result = favicon.run()

    assert result == {
        "data": expected_data,
        "url": "https://example.com/favicon.ico",
        "hash": expected_hash,
    }
