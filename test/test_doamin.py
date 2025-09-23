from app.services.altDNS import DnsGen, AltDNS, alt_dns


def test_dns_gen_creates_permutations():
    generator = DnsGen({"www.example.com"}, ["api"], base_domain="example.com")
    results = list(generator.run())

    assert any("api" in result for result in results)


def test_alt_dns_filters_records_above_threshold(monkeypatch):
    duplicates = [
        {"domain": f"d{i}.example.com", "type": "A", "record": "1.1.1.1"}
        for i in range(15)
    ]
    duplicates.append({"domain": "keep.example.com", "type": "A", "record": "2.2.2.2"})

    monkeypatch.setattr("app.services.altDNS.AltDNS.run", lambda self: duplicates)

    filtered = alt_dns(["sub.example.com"], base_domain="example.com")

    assert filtered == [{"domain": "keep.example.com", "type": "A", "record": "2.2.2.2"}]


def test_alt_dns_run_passes_generated_domains(monkeypatch):
    captured = {}

    class DummyMassDNS:
        def __init__(self, domains, **kwargs):
            captured["domains"] = list(domains)

        def run(self):
            return [{"domain": d, "type": "A", "record": "1.1.1.1"} for d in captured["domains"]]

    monkeypatch.setattr("app.services.altDNS.MassDNS", DummyMassDNS)
    monkeypatch.setattr("app.services.altDNS.DnsGen.run", lambda self: iter(["api.example.com"]))

    result = AltDNS(["www.example.com"], base_domain="example.com", words=[]).run()

    assert captured["domains"] == ["api.example.com"]
    assert result[0]["domain"] == "api.example.com"
