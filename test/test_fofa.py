from base64 import b64decode

from app.config import Config
from app.services.fofaClient import FofaClient, fofa_query


def test_fofa_client_search_stops_on_short_page(monkeypatch):
    calls = []

    def fake_api(self, path, params):
        query = b64decode(params["qbase64"]).decode()
        calls.append((path, query, params["page"]))
        page = params["page"]
        results = [f"item-{page}-{i}" for i in range(self.page_size)] if page < 3 else []
        return {"query": query, "size": 5, "results": results}

    monkeypatch.setattr(FofaClient, "_api", fake_api)

    client = FofaClient("key", page_size=2, max_page=5)
    pages = list(client.search('body="test"'))

    assert len(pages) == 2
    assert pages[0] == ["item-1-0", "item-1-1"]
    assert calls[0][1] == 'body="test"'


def test_fofa_query_returns_message_without_key(monkeypatch):
    monkeypatch.setattr("app.services.fofaClient.Config.FOFA_KEY", "")

    result = fofa_query("query")

    assert "please set fofa key" in result


def test_fofa_query_flattens_results(monkeypatch):
    monkeypatch.setattr("app.services.fofaClient.Config.FOFA_KEY", "key")

    def fake_search(self, query):
        yield ["a", "b"]
        yield ["c"]

    monkeypatch.setattr(FofaClient, "search", fake_search)

    result = fofa_query("query", page_size=1, max_page=2)

    assert result == ["a", "b", "c"]
