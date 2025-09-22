from app.helpers.task import build_task_data, target2list
from app.modules import TaskTag, TaskType


def test_target2list_removes_duplicates():
    target = "a.com, b.com a.com"
    assert set(target2list(target)) == {"a.com", "b.com"}


def test_build_task_data_disables_options_for_ip():
    options = {
        "domain_brute": True,
        "alt_dns": True,
        "dns_query_plugin": True,
        "arl_search": True,
    }

    data = build_task_data(
        task_name="demo",
        task_target="1.1.1.1",
        task_type=TaskType.IP,
        task_tag=TaskTag.TASK,
        options=options,
    )

    assert data["options"]["domain_brute"] is False
    assert data["options"]["dns_query_plugin"] is False
    assert data["status"] == "waiting"
