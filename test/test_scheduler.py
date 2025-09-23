from app.helpers.scheduler import have_same_site_update_monitor, have_same_wih_update_monitor


def test_have_same_site_update_monitor(monkeypatch):
    class DummyScheduler:
        def find_one(self, query):
            return {"scope_id": query["scope_id"]}

    monkeypatch.setattr("app.helpers.scheduler.utils.conn_db", lambda name: DummyScheduler())

    assert have_same_site_update_monitor("scope") is True


def test_have_same_wih_update_monitor(monkeypatch):
    class DummyScheduler:
        def find_one(self, query):
            return None

    monkeypatch.setattr("app.helpers.scheduler.utils.conn_db", lambda name: DummyScheduler())

    assert have_same_wih_update_monitor("scope") is False
