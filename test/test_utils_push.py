import pytest

from app.utils.push import Push, dict2dingding_mark, dict2table, message_push


@pytest.fixture
def sample_asset_map():
    return {
        "task_name": "Demo Task",
        "site": [
            {
                "site": "https://demo",
                "title": "Welcome",
                "status": 200,
                "favicon": {"hash": 123},
            }
        ],
        "domain": [
            {
                "domain": "demo.example",
                "type": "A",
                "record": ["1.1.1.1"],
            }
        ],
        "ip": [
            {
                "ip": "1.1.1.1",
                "port_info": [{"port_id": 80}, {"port_id": 443}],
                "geo_asn": {"organization": "Example Org"},
            }
        ],
    }


@pytest.fixture
def sample_asset_counter():
    return {"site": 1, "domain": 1, "ip": 1}


def test_push_builders_extract_expected_fields(sample_asset_map, sample_asset_counter):
    p = Push(sample_asset_map, sample_asset_counter)

    assert p.site_info_list == [
        {
            "站点": "https://demo",
            "标题": "Welcome",
            "状态码": 200,
            "favicon": 123,
        }
    ]

    assert p.domain_info_list == [
        {"域名": "demo.example", "解析类型": "A", "记录值": "1.1.1.1"}
    ]

    assert p.ip_info_list == [
        {
            "IP": "1.1.1.1",
            "端口数目": 2,
            "开放端口": "80,443",
            "组织": "Example Org",
        }
    ]


def test_push_dingding_invokes_helper(monkeypatch, sample_asset_map, sample_asset_counter):
    p = Push(sample_asset_map, sample_asset_counter)

    monkeypatch.setattr("app.config.Config.DINGDING_ACCESS_TOKEN", "token")
    monkeypatch.setattr("app.config.Config.DINGDING_SECRET", "secret")

    calls = {"count": 0}

    def fake_push():
        calls["count"] += 1
        return True

    monkeypatch.setattr(p, "_push_dingding", fake_push)

    assert p.push_dingding() is True
    assert calls["count"] == 1


def test_dict2dingding_mark_formats_rows(sample_asset_map):
    site_list = Push(sample_asset_map, {"site": 1}).site_info_list
    result = dict2dingding_mark(site_list)

    lines = result.splitlines()
    assert lines[0].startswith("站点")
    assert any(line.startswith("1.") for line in lines)
    assert "https://demo" in result


def test_dict2table_escapes_html(sample_asset_map):
    html_map = sample_asset_map.copy()
    html_map["site"] = [
        {
            "site": "https://demo",
            "title": "<b>Welcome</b>",
            "status": 200,
            "favicon": {"hash": "<123>"},
        }
    ]

    table_html = dict2table(Push(html_map, {"site": 1}).site_info_list)
    assert "<b>" not in table_html
    assert "&#x3c;b&#x3e;Welcome&#x3c;/b&#x3e;" in table_html


def test_message_push_triggers_all_channels(monkeypatch, sample_asset_map, sample_asset_counter):
    created = []

    class DummyPush:
        def __init__(self, asset_map, asset_counter):
            self.asset_map = asset_map
            self.asset_counter = asset_counter
            self.calls = []
            created.append(self)

        def push_dingding(self):
            self.calls.append("dingding")

        def push_email(self):
            self.calls.append("email")

        def push_feishu(self):
            self.calls.append("feishu")

        def push_wx_work(self):
            self.calls.append("wx")

    monkeypatch.setattr("app.utils.push.Push", DummyPush)

    message_push(sample_asset_map, sample_asset_counter)

    assert created and created[0].calls == ["dingding", "email", "feishu", "wx"]
