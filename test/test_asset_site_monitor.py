import pytest

from app.services.asset_site_monitor import AssetSiteMonitor


@pytest.fixture
def monitor(monkeypatch):
    monkeypatch.setattr(
        "app.services.asset_site_monitor.get_scope_by_scope_id",
        lambda scope_id: {"name": "demo", "_id": scope_id},
    )
    return AssetSiteMonitor("scope-1")


def test_compare_status_records_change(monkeypatch, monitor):
    recorded = []
    monkeypatch.setattr(monitor, "update_asset_site", lambda asset_id, info: recorded.append((asset_id, info)))

    old_site = {"_id": "asset-1", "site": "https://demo", "status": 404, "title": "Old"}
    new_site = {"site": "https://demo", "status": 200, "title": "Old"}

    assert monitor.compare_status(new_site, old_site)
    assert monitor.status_change_list == [
        {"site": "https://demo", "status": 200, "old_status": 404}
    ]
    assert recorded == [("asset-1", new_site)]


def test_compare_title_records_change(monkeypatch, monitor):
    recorded = []
    monkeypatch.setattr(monitor, "update_asset_site", lambda asset_id, info: recorded.append((asset_id, info)))

    old_site = {"_id": "asset-2", "site": "https://demo", "status": 200, "title": "Old"}
    new_site = {"site": "https://demo", "status": 200, "title": "New"}

    assert monitor.compare_title(new_site, old_site)
    assert monitor.title_change_list == [
        {"site": "https://demo", "title": "New", "old_title": "Old"}
    ]
    assert recorded == [("asset-2", new_site)]


def test_build_change_list_collects_sites(monkeypatch, monitor):
    class DummyCompare:
        def __init__(self, scope_id):
            assert scope_id == "scope-1"

        def run(self):
            return {
                "https://demo": {
                    "_id": "asset-3",
                    "site": "https://demo",
                    "status": 500,
                    "title": "Old",
                }
            }

    monkeypatch.setattr("app.services.asset_site_monitor.AssetSiteCompare", DummyCompare)
    monkeypatch.setattr(
        "app.services.asset_site_monitor.fetch_site",
        lambda sites: [
            {
                "site": sites[0],
                "status": 200,
                "title": "Fresh",
                "tag": ["入口"],
            }
        ],
    )
    updates = []
    monkeypatch.setattr(monitor, "update_asset_site", lambda asset_id, info: updates.append((asset_id, info)))

    monitor.build_change_list()

    assert updates == [("asset-3", monitor.site_change_info_list[0])]
    assert monitor.site_change_info_list[0]["title"] == "Fresh"


def test_html_reports_include_changes(monkeypatch, monitor):
    monitor.status_change_list.append({"site": "https://demo", "status": 200, "old_status": 500})
    monitor.title_change_list.append({"site": "https://demo", "title": "Fresh", "old_title": "Old"})

    status_html = monitor.build_status_html_report()
    title_html = monitor.build_title_html_report()

    assert "https://demo" in status_html
    assert "Fresh" in title_html
