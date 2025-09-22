from types import SimpleNamespace

from app.tasks.asset_wih import AssetWihUpdateTask


def test_run_wih_monitor_updates_status(monkeypatch):
    task = AssetWihUpdateTask("task-id", "scope-id")

    calls = {"status": [], "services": []}

    class DummyBase:
        def update_task_field(self, field, value):
            calls.setdefault(field, []).append(value)

        def update_services(self, name, elapsed):
            calls["services"].append((name, elapsed))

    task.base_update_task = DummyBase()

    monkeypatch.setattr("app.tasks.asset_wih.get_scope_by_scope_id", lambda scope_id: {"name": "demo"})
    monkeypatch.setattr("app.tasks.asset_wih.asset_wih_monitor", lambda scope_id: [SimpleNamespace()])
    monkeypatch.setattr("app.tasks.asset_wih.time.time", lambda: 1.0)

    task.run_wih_monitor()

    assert task.wih_results
    assert calls["status"] == ["wih_monitor"]
    assert calls["services"] == [("wih_monitor", 0.0)]


def test_run_wih_domain_update_triggers_sync(monkeypatch):
    task = AssetWihUpdateTask("task-id", "scope-id")
    task.wih_results = [
        SimpleNamespace(recordType="domain", content="new.example.com"),
        SimpleNamespace(recordType="domain", content="existing.example.com"),
        SimpleNamespace(recordType="ip", content="1.1.1.1"),
    ]
    task._scope_sub_domains = {"existing.example.com"}

    monkeypatch.setattr("app.tasks.asset_wih.get_scope_by_scope_id", lambda scope_id: {"scope_type": "domain"})
    domain_calls = []

    def fake_domain_update(task_id, domains, source):
        domain_calls.append((task_id, tuple(domains), source))

    monkeypatch.setattr("app.tasks.asset_wih.domain_site_update", fake_domain_update)

    sync_calls = []
    monkeypatch.setattr("app.tasks.asset_wih.sync_asset", lambda task_id, scope_id: sync_calls.append((task_id, scope_id)))

    task.run_wih_domain_update()

    assert domain_calls == [("task-id", ("new.example.com",), "wih")]
    assert sync_calls == [("task-id", "scope-id")]
