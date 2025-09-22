from app.modules import TaskStatus
from app.utils.github_task import CeleryAction, submit_github_task


def make_task(keyword="demo"):
    return {
        "name": "test",
        "keyword": keyword,
        "start_time": "-",
        "end_time": "-",
        "status": TaskStatus.WAITING,
    }


def test_submit_github_task_inserts_and_updates(monkeypatch):
    inserted = []
    updated = []
    celery_calls = []

    class DummyCollection:
        def insert_one(self, data):
            data["_id"] = "0" * 24
            inserted.append(data.copy())

        def update_one(self, query, update):
            updated.append((query, update))

        def delete_one(self, query):
            pass

    monkeypatch.setattr("app.utils.github_task.utils.conn_db", lambda name: DummyCollection())
    monkeypatch.setattr("app.utils.github_task.celerytask.arl_github", lambda options: celery_calls.append(options))

    task = make_task()
    result = submit_github_task(task_data=task, action=CeleryAction.GITHUB_TASK_TASK, delay_flag=False)

    assert result["celery_id"] == "fake_celery_id"
    assert result["task_id"] == "0" * 24
    assert celery_calls and celery_calls[0]["data"]["keyword"] == "demo"
    assert updated[-1][1]["$set"]["celery_id"] == "fake_celery_id"


def test_submit_github_task_invalid_action():
    msg = submit_github_task(task_data=make_task(), action="invalid")
    assert msg == "Not in action_map"
