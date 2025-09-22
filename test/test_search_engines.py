from types import SimpleNamespace

from app.services.searchEngines import BaiduSearch, search_engines


def test_baidu_search_match_urls_follow_redirect(monkeypatch):
    html = """
    <html>
      <span>百度为您找到相关结果约1个</span>
      <div id="content_left">
        <h3 class="t"><a href="http://redirect/1">Example</a></h3>
      </div>
    </html>
    """

    monkeypatch.setattr(
        "app.services.searchEngines.utils.http_req",
        lambda url, method='get', headers=None: SimpleNamespace(headers={"Location": "https://example.com"}),
    )

    search = BaiduSearch("site:example.com")
    urls = search.match_urls(html)

    assert urls == ["https://example.com"]


def test_search_engines_combines_unique_urls(monkeypatch):
    monkeypatch.setattr("app.services.searchEngines.bing_search", lambda domain: ["https://a.com", "https://b.com"])
    monkeypatch.setattr("app.services.searchEngines.baidu_search", lambda domain: ["https://a.com", "https://c.com"])

    urls = search_engines("example.com")

    assert {u.rstrip('/') for u in urls} == {"https://a.com", "https://b.com", "https://c.com"}
