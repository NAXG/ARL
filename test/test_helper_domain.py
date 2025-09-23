from app.helpers.domain import find_domain_by_task_id, find_private_domain_by_task_id, find_public_ip_by_task_id


def test_find_private_domain_deduplicates(monkeypatch):
    class DummyIPCollection:
        def find(self, query):
            return [
                {"domain": ["a.com", "b.com"]},
                {"domain": ["a.com"]},
                {"domain": None},
            ]

    monkeypatch.setattr(
        "app.helpers.domain.utils.conn_db",
        lambda name: DummyIPCollection() if name == "ip" else None,
    )

    assert sorted(find_private_domain_by_task_id("task")) == ["a.com", "b.com"]


def test_find_public_ip_distinct(monkeypatch):
    class DummyIPCollection:
        def distinct(self, field, query):
            return ["1.1.1.1", "2.2.2.2"]

    monkeypatch.setattr(
        "app.helpers.domain.utils.conn_db",
        lambda name: DummyIPCollection() if name == "ip" else None,
    )

    assert find_public_ip_by_task_id("task") == ["1.1.1.1", "2.2.2.2"]


def test_find_domain_by_task_id(monkeypatch):
    class DummyDomainCollection:
        def distinct(self, field, query):
            return ["a.com", "b.com"]

    monkeypatch.setattr(
        "app.helpers.domain.utils.conn_db",
        lambda name: DummyDomainCollection() if name == "domain" else None,
    )

    assert find_domain_by_task_id("task") == ["a.com", "b.com"]
