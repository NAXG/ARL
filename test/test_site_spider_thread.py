from app.services.siteUrlSpider import URLInfo, URLSimilarList, site_spider_thread


def test_url_similar_list_removes_duplicates():
    urls = URLSimilarList()
    info = URLInfo("https://example.com", "https://example.com/a", "document")
    urls.add(info)
    urls.add(URLInfo("https://example.com", "https://example.com/a", "document"))

    assert len(list(urls)) == 1


def test_site_spider_thread_aggregates_sites(monkeypatch):
    monkeypatch.setattr(
        "app.services.siteUrlSpider.BaseThread._run",
        lambda self: [self.work(target) for target in self.targets],
    )
    monkeypatch.setattr(
        "app.services.siteUrlSpider.site_spider",
        lambda entry_urls, deep_num: [f"{entry_urls[0]}/page"],
    )

    results = site_spider_thread([["https://demo"]], deep_num=1)

    assert results == {"https://demo": ["https://demo/page"]}
