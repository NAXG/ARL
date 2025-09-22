from app.helpers.asset_wih_monitor import submit_asset_wih_monitor_job
from app.services.asset_wih_monitor import asset_wih_monitor, domain_in_scope_domain


def test_domain_in_scope_domain_matches_suffix():
    scope = ["example.com", "foo.bar"]
    assert domain_in_scope_domain("a.example.com", scope)
    assert not domain_in_scope_domain("a.something", scope)


def test_asset_wih_monitor_filters_and_saves(monkeypatch):
    inserted = []

    class DummyCollection:
        def find_one(self, query):
            return None

        def insert_one(self, document):
            inserted.append(document)

    monkeypatch.setattr("app.services.asset_wih_monitor.utils.conn_db", lambda name: DummyCollection())
    monkeypatch.setattr("app.services.asset_wih_monitor.utils.curr_date_obj", lambda: "2024-01-01")
    monkeypatch.setattr(
        "app.services.asset_wih_monitor.get_scope_by_scope_id",
        lambda scope_id: {"name": "scope", "scope_type": "domain", "scope_array": ["example.com"]},
    )
    monkeypatch.setattr("app.services.asset_wih_monitor.asset_site.find_site_by_scope_id", lambda scope_id: ["https://x"])
    monkeypatch.setattr("app.services.asset_wih_monitor.asset_wih.get_wih_record_fnv_hash", lambda scope_id: ["existing"])

    class FakeRecord:
        def __init__(self, record_type, content, fnv_hash):
            self.recordType = record_type
            self.content = content
            self.fnv_hash = fnv_hash
            self.site = "https://x"
            self.source = "wih"

        def dump_json(self):
            return {
                "record_type": self.recordType,
                "content": self.content,
                "site": self.site,
                "source": self.source,
                "fnv_hash": str(self.fnv_hash),
            }

    records = [
        FakeRecord("domain", "new.example.com", 123),
        FakeRecord("domain", "old.example.com", "existing"),
        FakeRecord("domain", "skip.outside", 456),
        FakeRecord("ip", "1.1.1.1", 789),
    ]

    monkeypatch.setattr("app.services.asset_wih_monitor.run_wih", lambda sites: records)
    monkeypatch.setattr("app.services.asset_wih_monitor.check_domain_black", lambda domain: domain == "skip.outside")

    results = asset_wih_monitor("scope-id")

    assert [r.fnv_hash for r in results] == [123, 789]
    assert inserted and inserted[0]["scope_id"] == "scope-id"


def test_submit_asset_wih_monitor_job_builds_task(monkeypatch):
    captured = {}

    def fake_submit(task_data):
        captured.update(task_data)

    monkeypatch.setattr("app.helpers.task.submit_task", fake_submit)

    submit_asset_wih_monitor_job("scope", "name", "sched")

    assert captured["options"] == {"scope_id": "scope", "scheduler_id": "sched"}
