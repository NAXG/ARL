from app.helpers.task import submit_task
from app.modules import CeleryAction, TaskStatus, TaskTag, TaskType


class DummyCollection:
    def __init__(self):
        self.inserted = []
        self.updated = []

    def insert_one(self, document):
        document["_id"] = "f" * 24
        self.inserted.append(document.copy())

    def update_one(self, query, update):
        self.updated.append((query, update))

    def delete_one(self, query):
        pass


class DummyArlTask:
    def __init__(self):
        self.called_with = None

    def delay(self, *, options):
        self.called_with = options
        return "celery-domain"


def test_submit_task_dispatches_domain_jobs(monkeypatch):
    task_collection = DummyCollection()

    def fake_conn(name):
        assert name == "task"
        return task_collection

    monkeypatch.setattr("app.helpers.task.utils.conn_db", fake_conn)
    dummy_task = DummyArlTask()
    monkeypatch.setattr("app.celerytask.arl_task", dummy_task)

    task_data = {
        "name": "domain task",
        "target": "example.com",
        "start_time": "-",
        "status": TaskStatus.WAITING,
        "type": TaskType.DOMAIN,
        "task_tag": TaskTag.TASK,
        "options": {
            "domain_brute": True,
            "alt_dns": False,
            "port_scan": False,
        },
        "end_time": "-",
        "service": [],
        "celery_id": "",
    }

    result = submit_task(task_data)

    assert result["task_id"] == "f" * 24
    assert result["celery_id"] == "celery-domain"
    assert dummy_task.called_with["celery_action"] == CeleryAction.DOMAIN_TASK
