from app.services.findVhost import Page, find_vhost


def make_page(domain, title, body_length=200):
    body = (f"<html><title>{title}</title><body>{'x' * body_length}</body></html>").encode()
    return Page(url="http://1.1.1.1", domain=domain, content=body, status_code=200, content_type="text/html")


def test_page_equality_respects_thresholds():
    a = make_page("a.com", "Alpha", body_length=200)
    b = make_page("a.com", "Alpha", body_length=203)
    c = make_page("a.com", "Beta", body_length=300)

    assert a == b
    assert a != c


def test_find_vhost_deduplicates_by_domain_title(monkeypatch):
    page_a = make_page("a.com", "Title")
    page_a_dup = make_page("a.com", "Title")
    page_b = make_page("b.com", "Other", body_length=400)

    def fake_thread_map(func, items, arg, concurrency):
        return {
            "1.1.1.1": {page_a},
            "2.2.2.2": {page_a_dup, page_b},
        }

    monkeypatch.setattr("app.services.findVhost.thread_map", fake_thread_map)

    results = find_vhost(["1.1.1.1", "2.2.2.2"], ["a.com", "b.com"])

    rows = {tuple(sorted(item.items())) for item in results}
    expected = {tuple(sorted(page_a.dump_json_obj().items())), tuple(sorted(page_b.dump_json_obj().items()))}
    assert rows == expected
