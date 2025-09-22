from bson import ObjectId
import pytest

from app.tasks.asset_site import AssetSiteUpdateTask


class DummyCollection:
    def __init__(self):
        self.updated = []
        self.inserted = []

    def update_one(self, query, update):
        self.updated.append((query, update))

    def insert_one(self, document):
        self.inserted.append(document)


@pytest.fixture
def task_env(monkeypatch):
    collections = {"task": DummyCollection(), "site": DummyCollection()}

    monkeypatch.setattr("app.utils.conn_db", lambda name: collections[name])
    monkeypatch.setattr("app.utils.curr_date", lambda: "2024-01-01")

    task_id = "64c254f26c425108fb1a4821"

    return task_id, collections


def test_update_status_writes_to_task_collection(task_env):
    task_id, collections = task_env
    task = AssetSiteUpdateTask(task_id=task_id, scope_id="scope")

    task.update_status("running")

    query, update = collections["task"].updated[0]
    assert query == {"_id": ObjectId(task_id)}
    assert update == {"$set": {"status": "running"}}


def test_set_start_and_end_time(task_env):
    task_id, collections = task_env
    task = AssetSiteUpdateTask(task_id=task_id, scope_id="scope")

    task.set_start_time()
    task.set_end_time()

    assert collections["task"].updated == [
        ({"_id": ObjectId(task_id)}, {"$set": {"start_time": "2024-01-01"}}),
        ({"_id": ObjectId(task_id)}, {"$set": {"end_time": "2024-01-01"}}),
    ]


def test_save_task_site_attaches_task_id(task_env):
    task_id, collections = task_env
    task = AssetSiteUpdateTask(task_id=task_id, scope_id="scope")

    task.save_task_site([
        {"site": "https://demo", "status": 200, "title": "Demo"}
    ])

    inserted = collections["site"].inserted[0]
    assert inserted["task_id"] == task_id
    assert inserted["site"] == "https://demo"
