from app.modules import DomainInfo
from app.tasks.domain import DomainTask


def make_domain_info(domain, ip):
    return DomainInfo(domain=domain, record=[ip], type="A", ips=[ip])


def test_clear_domain_info_by_record_skips_wildcard_and_repeated(monkeypatch):
    task = DomainTask(base_domain="example.com", task_id="task", options={})
    task._not_found_domain_ips = ["1.1.1.1"]
    task.record_map["2.2.2.2"] = 35

    infos = [
        make_domain_info("wild.example.com", "1.1.1.1"),
        make_domain_info("repeat.example.com", "2.2.2.2"),
        make_domain_info("ok.example.com", "3.3.3.3"),
    ]

    filtered = task.clear_domain_info_by_record(infos)

    assert [info.domain for info in filtered] == ["ok.example.com"]


def test_build_domain_info_ignores_duplicates_and_blacklist(monkeypatch):
    task = DomainTask(base_domain="example.com", task_id="task", options={})
    task.task_tag = "monitor"
    monkeypatch.setattr("app.tasks.domain.utils.check_domain_black", lambda domain: domain.startswith("bad"))

    result = task.build_domain_info([
        "good.example.com",
        {"domain": "good.example.com"},
        "bad.example.com",
    ])

    assert len(result) == 1
    assert result[0].domain == "good.example.com"
