from app.tasks.scheduler import IPExecutor


class DummyCollection:
    def __init__(self, items=None):
        self.items = items or []

    def find(self, query, projection=None):
        return DummyCursor(self.items)

    def insert_one(self, data):
        data["_id"] = "generated"


class DummyCursor:
    def __init__(self, items):
        self.items = items

    def __iter__(self):
        return iter(self.items)

    def limit(self, _):
        return self


def test_set_asset_ip_builds_port_set(monkeypatch):
    executor = IPExecutor("1.1.1.1", "scope", "task", {})
    items = [{"ip": "1.1.1.1", "port_info": [{"port_id": 80}, {"port_id": 443}], "_id": "x"}]

    monkeypatch.setattr("app.tasks.scheduler.utils.conn_db", lambda name: DummyCollection(items) if name == "asset_ip" else DummyCollection())

    executor.set_asset_ip()

    assert executor.asset_ip_port_set == {"1.1.1.1:80", "1.1.1.1:443"}


def test_insert_task_data_assigns_task_id(monkeypatch):
    captured = {}

    class TaskCollection(DummyCollection):
        def insert_one(self, data):
            super().insert_one(data)
            captured.update(data)

    monkeypatch.setattr("app.tasks.scheduler.conn", lambda name: TaskCollection())

    executor = IPExecutor("1.1.1.1", "scope", "task", {"site_identify": True})
    executor.insert_task_data()

    assert executor.task_id == "generated"
    assert captured["options"]["site_identify"] is True
