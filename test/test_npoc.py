import json

from app.services import npoc


class DummyPlugin:
    def __init__(self, name):
        self._plugin_name = name
        self.plugin_type = None


def test_filter_plugin_by_name(monkeypatch):
    n = npoc.NPoC()
    n._plugins = [DummyPlugin("a"), DummyPlugin("b")]

    result = n.filter_plugin_by_name(["a"])

    assert len(result) == 1
    assert result[0]._plugin_name == "a"


def test_run_poc_reads_json_results(monkeypatch):
    n = npoc.NPoC(tmp_dir="/")
    n.filter_plugin_by_name = lambda names: [DummyPlugin(name) for name in names]
    n.plugin_name_set = {"demo"}
    n._plugins = [DummyPlugin("demo")]

    class DummyRunner:
        def __init__(self, plugins, targets, concurrency):
            self.plugins = plugins
            self.targets = targets
            self.concurrency = concurrency

        def run(self):
            return None

    monkeypatch.setattr("app.services.npoc.PluginRunner.PluginRunner", DummyRunner)
    monkeypatch.setattr("app.services.npoc.os.path.exists", lambda path: True)
    monkeypatch.setattr("app.services.npoc.utils.load_file", lambda path: [json.dumps({"target": "demo"})])
    monkeypatch.setattr("app.services.npoc.os.unlink", lambda path: None)
    monkeypatch.setattr("app.services.npoc.utils.random_choices", lambda k=6: "abc")

    results = n.run_poc(["demo"], targets=["https://example.com"])

    assert results == [{"target": "demo"}]
