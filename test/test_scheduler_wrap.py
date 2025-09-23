from types import SimpleNamespace

from app.modules import TaskStatus
from app.tasks import scheduler


class DummyCollection:
    def __init__(self):
        self.inserted = []

    def insert_one(self, document):
        document["_id"] = "a" * 24
        self.inserted.append(document.copy())


def test_wrap_domain_executors_runs_monitor_flow(monkeypatch):
    task_collection = DummyCollection()

    def fake_conn(name):
        assert name == "task"
        return task_collection

    monkeypatch.setattr("app.tasks.scheduler.conn", fake_conn)
    monkeypatch.setattr("app.tasks.scheduler.current_task", SimpleNamespace(request=SimpleNamespace(id="celery-1")))

    domain_calls = {}

    class DummyDomainExecutor:
        def __init__(self, base_domain, task_id, options):
            domain_calls["args"] = (base_domain, task_id, options)

        def run(self):
            return {"new.example.com"}

    sync_calls = {}
    webhook_calls = {}

    monkeypatch.setattr("app.tasks.scheduler.DomainExecutor", DummyDomainExecutor)
    monkeypatch.setattr("app.tasks.scheduler.update_job_run", lambda job_id: sync_calls.setdefault("job", job_id))

    def fake_sync_asset(task_id, scope_id, update_flag=False, category=None, push_flag=False, task_name=""):
        sync_calls.update({
            "task_id": task_id,
            "scope_id": scope_id,
            "update_flag": update_flag,
            "task_name": task_name,
        })

    monkeypatch.setattr("app.tasks.scheduler.sync_asset", fake_sync_asset)
    monkeypatch.setattr(
        "app.tasks.scheduler.webhook.domain_asset_web_hook",
        lambda task_id, scope_id: webhook_calls.setdefault("args", (task_id, scope_id)),
    )

    scheduler.wrap_domain_executors(
        base_domain="example.com",
        job_id="b" * 24,
        scope_id="c" * 24,
        options={"alt_dns": True},
        name="Monitor Example",
    )

    inserted = task_collection.inserted[0]
    assert inserted["target"] == "example.com"
    assert inserted["status"] == TaskStatus.WAITING
    assert domain_calls["args"][0] == "example.com"
    assert sync_calls["scope_id"] == "c" * 24
    assert webhook_calls["args"] == ("a" * 24, "c" * 24)
