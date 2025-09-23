from app.services.syncAsset import sync_asset


class DummyCursor:
    def __init__(self, items):
        self._items = items

    def __iter__(self):
        return iter(self._items)

    def limit(self, _):
        return self


class DummyCollection:
    def __init__(self, items=None):
        self.items = items or []
        self.inserted = []

    def find(self, query, projection=None):
        if "task_id" in query:
            results = [item for item in self.items if item.get("task_id") == query["task_id"]]
        else:
            results = []
        return DummyCursor(results)

    def find_one(self, query, projection=None):
        if "scope_id" in query:
            for item in self.items:
                if item.get("scope_id") == query["scope_id"]:
                    return item
        if "site" in query:
            return None
        return None

    def insert_one(self, document):
        self.inserted.append(document.copy())

    def find_one_and_replace(self, query, document):
        pass


def test_sync_asset_inserts_new_sites(monkeypatch):
    site_docs = [
        {
            "_id": "1",
            "task_id": "task",
            "site": "https://demo",
            "title": "Demo",
            "status": 200,
            "http_server": "nginx",
            "body_length": 100,
        }
    ]

    collections = {
        "site": DummyCollection(site_docs),
        "asset_site": DummyCollection([]),
        "domain": DummyCollection([]),
        "asset_domain": DummyCollection([]),
        "ip": DummyCollection([]),
        "asset_ip": DummyCollection([]),
        "wih": DummyCollection([]),
        "asset_wih": DummyCollection([]),
    }

    push_calls = []

    monkeypatch.setattr("app.services.syncAsset.utils.curr_date_obj", lambda: "2024-01-01T00:00:00")
    monkeypatch.setattr(
        "app.services.syncAsset.utils.message_push",
        lambda asset_map, asset_counter: push_calls.append((asset_map, asset_counter)),
    )

    def fake_conn(name):
        return collections.setdefault(name, DummyCollection())

    monkeypatch.setattr("app.services.syncAsset.conn", fake_conn)

    sync_asset("task", "scope", push_flag=True, category=["site"], task_name="Demo")

    inserted = collections["asset_site"].inserted[0]
    assert inserted["scope_id"] == "scope"
    assert push_calls[0][0]["site"][0]["site"] == "https://demo"
    assert push_calls[0][1]["site"] == 1
