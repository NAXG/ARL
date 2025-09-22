from app.services.dns_query import run_plugin, run_query_plugin


class DummyPlugin:
    def __init__(self, source_name, results):
        self.source_name = source_name
        self._results = results
        self.inited_with = None

    def init_key(self, **kwargs):
        self.inited_with = kwargs

    def query(self, target):
        return [f"{sub}.{target}" for sub in self._results]


def test_run_plugin_respects_config(monkeypatch):
    plugin = DummyPlugin("demo", ["www"])

    monkeypatch.setattr("app.services.dns_query.Config.QUERY_PLUGIN_CONFIG", {"demo": {"enable": False}})

    source, results = run_plugin(plugin, "example.com")

    assert source == "demo"
    assert results == []


def test_run_query_plugin_deduplicates_domains(monkeypatch):
    plugins = [
        DummyPlugin("demo1", ["www", "api"]),
        DummyPlugin("demo2", ["www", "cdn"]),
    ]

    monkeypatch.setattr("app.services.dns_query.Config.QUERY_PLUGIN_CONFIG", {})
    monkeypatch.setattr("app.services.dns_query.utils.load_query_plugins", lambda path: plugins)

    results = run_query_plugin("example.com", sources=["demo1", "demo2"])

    domains = {item["domain"] for item in results}
    assert domains == {"www.example.com", "api.example.com", "cdn.example.com"}
