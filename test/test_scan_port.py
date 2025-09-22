from app.modules import DomainInfo
from app.tasks.domain import ScanPort, scan_port


def make_domain(domain, record, record_type, ips):
    return DomainInfo(domain=domain, record=record, type=record_type, ips=ips)


def test_scan_port_get_cdn_name_prefers_cname(monkeypatch):
    domain_info = make_domain("demo", ["cdn.example"], "CNAME", ["1.1.1.1"])
    scanner = ScanPort([domain_info], option={})

    monkeypatch.setattr("app.tasks.domain.utils.get_cdn_name_by_ip", lambda ip: "")
    monkeypatch.setattr("app.tasks.domain.utils.get_cdn_name_by_cname", lambda cname: "ExampleCDN")

    assert scanner.get_cdn_name("1.1.1.1", domain_info) == "ExampleCDN"


def test_scan_port_run_injects_fake_cdn_entries(monkeypatch):
    domain_info = make_domain("demo", ["cdn.example"], "CNAME", ["1.1.1.1"])

    monkeypatch.setattr("app.tasks.domain.utils.get_cdn_name_by_ip", lambda ip: "")
    monkeypatch.setattr("app.tasks.domain.utils.get_cdn_name_by_cname", lambda cname: "ExampleCDN")
    monkeypatch.setattr("app.tasks.domain.services.port_scan", lambda ips, **kwargs: [])

    results = scan_port([domain_info], {"skip_scan_cdn_ip": True})

    assert len(results) == 1
    info = results[0]
    assert info.cdn_name == "ExampleCDN"
    assert {port.port_id for port in info.port_info_list} == {80, 443}
