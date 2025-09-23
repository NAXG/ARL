from app.helpers.task import restart_task
from app.modules import TaskStatus, TaskTag, TaskType


def test_restart_task_requires_existing(monkeypatch):
    monkeypatch.setattr("app.helpers.task.get_task_data", lambda task_id: None)

    try:
        restart_task("missing")
    except Exception as exc:
        assert "missing" in str(exc)
    else:
        assert False, "expected exception"


def test_restart_task_returns_prefixed_copy(monkeypatch):
    task = {
        "name": "demo",
        "target": "example",
        "type": TaskType.DOMAIN,
        "task_tag": TaskTag.TASK,
        "options": {},
        "start_time": "2020",
        "status": "done",
        "end_time": "2020",
        "service": [1],
        "celery_id": "abc",
        "_id": "0" * 24,
    }

    monkeypatch.setattr("app.helpers.task.get_task_data", lambda task_id: task.copy())
    def fake_submit(task_data):
        task_data["task_id"] = "new"
        return task_data

    monkeypatch.setattr("app.helpers.task.submit_task", fake_submit)

    result = restart_task("task")

    assert result["name"] == "重新运行-" + task["name"]
    assert result["status"] == TaskStatus.WAITING
    assert result["service"] == []
    assert result["task_id"] == "new"
