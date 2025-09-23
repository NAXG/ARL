from app.utils.arl import gen_cip_map


class DummyCursor:
    def __init__(self, data):
        self.data = list(data)

    def find(self, query=None, projection=None):
        return list(self.data)


def test_gen_cip_map_groups_ip_ranges(monkeypatch):
    data = [
        {"ip": "1.1.1.1", "domain": ["a.example"]},
        {"ip": "1.1.1.2", "domain": ["b.example"]},
    ]

    monkeypatch.setattr("app.utils.arl.conn_db", lambda name: DummyCursor(data))

    result = gen_cip_map("1234567890abcdef12345678")

    assert result == {
        "1.1.1.0/24": {
            "domain_set": {"a.example", "b.example"},
            "ip_set": {"1.1.1.1", "1.1.1.2"},
        }
    }


def test_gen_cip_map_handles_missing_domains(monkeypatch):
    data = [
        {"ip": "2.2.2.2", "domain": None},
    ]

    monkeypatch.setattr("app.utils.arl.conn_db", lambda name: DummyCursor(data))

    result = gen_cip_map()

    assert result == {
        "2.2.2.0/24": {
            "domain_set": set(),
            "ip_set": {"2.2.2.2"},
        }
    }
