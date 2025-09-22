from types import SimpleNamespace

from app.utils import get_ip_city, get_ip_asn


class FakeReader:
    def __init__(self, path):
        self.path = path

    def city(self, ip):
        subdivision = SimpleNamespace(name="Region", iso_code="RG")
        return SimpleNamespace(
            city=SimpleNamespace(name="City"),
            subdivisions=SimpleNamespace(most_specific=subdivision),
            location=SimpleNamespace(latitude=1.23, longitude=3.21),
            country=SimpleNamespace(name="Country", iso_code="CC"),
        )

    def asn(self, ip):
        return SimpleNamespace(autonomous_system_number=64512, autonomous_system_organization="Demo Org")

    def close(self):
        pass


def test_get_ip_city_uses_reader(monkeypatch):
    monkeypatch.setattr("app.utils.ip.geoip2.database.Reader", FakeReader)

    result = get_ip_city("1.1.1.1")

    assert result == {
        "city": "City",
        "latitude": 1.23,
        "longitude": 3.21,
        "country_name": "Country",
        "country_code": "CC",
        "region_name": "Region",
        "region_code": "RG",
    }


def test_get_ip_asn_returns_number(monkeypatch):
    monkeypatch.setattr("app.utils.ip.geoip2.database.Reader", FakeReader)

    result = get_ip_asn("1.1.1.1")

    assert result == {"number": 64512, "organization": "Demo Org"}
