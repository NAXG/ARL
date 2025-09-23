from app.helpers.task import submit_task
from app.modules import CeleryAction, TaskStatus, TaskTag, TaskType


class DummyCollection:
    def __init__(self):
        self.inserted = []
        self.updated = []

    def insert_one(self, document):
        document["_id"] = "0" * 24
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
        return "celery-id"


def test_submit_task_dispatches_ip_jobs(monkeypatch):
    task_collection = DummyCollection()

    def fake_conn(name):
        assert name == "task"
        return task_collection

    monkeypatch.setattr("app.helpers.task.utils.conn_db", fake_conn)
    dummy_task = DummyArlTask()
    monkeypatch.setattr("app.celerytask.arl_task", dummy_task)

    task_data = {
        "name": "ip task",
        "target": "1.1.1.1",
        "start_time": "-",
        "status": TaskStatus.WAITING,
        "type": TaskType.IP,
        "task_tag": TaskTag.TASK,
        "options": {
            "port_scan": True,
            "service_detection": False,
            "os_detection": False,
        },
        "end_time": "-",
        "service": [],
        "celery_id": "",
    }

    result = submit_task(task_data)

    assert result["task_id"] == "0" * 24
    assert result["celery_id"] == "celery-id"
    assert dummy_task.called_with["celery_action"] == CeleryAction.IP_TASK

    query, update = task_collection.updated[-1]
    assert update["$set"]["celery_id"] == "celery-id"
