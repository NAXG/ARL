from app import services


def test_run_wih_uses_infohunter(monkeypatch):
    captured = {}

    class FakeRecord:
        def __init__(self, fnv_hash):
            self.fnv_hash = fnv_hash

    def fake_init(self, sites):
        captured["sites"] = sites

    monkeypatch.setattr("app.services.infoHunter.InfoHunter.__init__", fake_init)
    monkeypatch.setattr("app.services.infoHunter.InfoHunter.run", lambda self: [FakeRecord(1)])

    results = services.run_wih(["https://demo"])

    assert captured["sites"] == ["https://demo"]
    assert [r.fnv_hash for r in results] == [1]
