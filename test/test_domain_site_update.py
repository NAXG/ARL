from types import SimpleNamespace

from app.services.domainSiteUpdate import DomainSiteUpdate


def test_set_and_check_domains_filters_existing(monkeypatch):
    monitor = DomainSiteUpdate("task", ["a", "b"], "manual")

    monkeypatch.setattr("app.services.domainSiteUpdate.find_domain_by_task_id", lambda task_id: ["a"])

    monitor.set_and_check_domains()

    assert monitor.domains == ["b"]


def test_save_domain_info_inserts_records(monkeypatch):
    inserted = []

    class DummyCollection:
        def insert_one(self, data):
            inserted.append(data)

    monkeypatch.setattr("app.services.domainSiteUpdate.utils.conn_db", lambda name: DummyCollection())
    monkeypatch.setattr("app.services.domainSiteUpdate.utils.domain_parsed", lambda domain: {"fld": "example.com"})

    domain_obj = SimpleNamespace(
        domain="demo.example.com",
        dump_json=lambda flag: {"domain": "demo.example.com", "record": ["1.1.1.1"]},
    )

    monkeypatch.setattr("app.services.domainSiteUpdate.build_domain_info", lambda domains: [domain_obj])

    monitor = DomainSiteUpdate("task", ["demo.example.com"], "manual")
    monitor.save_domain_info()

    assert monitor.domain_info_list == [domain_obj]
    assert inserted[0]["task_id"] == "task"
    assert inserted[0]["source"] == "manual"
