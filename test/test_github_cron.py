from app.modules import CeleryAction
from app.utils.github_task import github_cron_run, find_github_scheduler


def test_github_cron_run_updates_scheduler(monkeypatch):
    captured_task = {}
    saved_item = {}

    monkeypatch.setattr(
        "app.utils.github_task.submit_github_task",
        lambda task_data, action: captured_task.update({"task": task_data, "action": action}),
    )

    class DummyCron:
        def __init__(self, expression):
            self.expression = expression

        def next(self, now=None, default_utc=False):
            return 120

    class DummyCollection:
        def find_one_and_replace(self, query, item):
            saved_item.update(item)

    monkeypatch.setattr("app.utils.github_task.CronTab", DummyCron)
    monkeypatch.setattr("app.utils.github_task.utils.conn_db", lambda name: DummyCollection())
    monkeypatch.setattr("app.utils.github_task.utils.curr_date", lambda: "2024-01-01")
    monkeypatch.setattr("app.utils.github_task.utils.time2date", lambda secs: "2024-01-02")
    monkeypatch.setattr("app.utils.github_task.time.time", lambda: 100)

    item = {"_id": "123", "name": "demo", "keyword": "repo", "run_number": 0, "cron": "* * * * *"}
    github_cron_run(item)

    assert captured_task["action"] == CeleryAction.GITHUB_TASK_MONITOR
    assert captured_task["task"]["github_scheduler_id"] == "123"
    assert saved_item["run_number"] == 1
    assert saved_item["next_run_date"] == "2024-01-02"


def test_find_github_scheduler_returns_item(monkeypatch):
    expected = {"_id": "abc"}

    class DummyCollection:
        def find_one(self, query):
            return expected

    monkeypatch.setattr("app.utils.github_task.utils.conn_db", lambda name: DummyCollection())

    result = find_github_scheduler("abc" * 8)  # 24 chars

    assert result is expected
