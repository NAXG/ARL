from app.routes.policy import add_policy_fields, change_policy_dict, gen_model_policy_keys


def test_gen_policy_keys_contains_web_info():
    keys = gen_model_policy_keys(add_policy_fields["policy"])
    assert "web_info_hunter" in keys
    assert keys


def test_change_policy_dict_merges_nested_fields():
    policy = {
        "domain_config": {"domain_brute": True, "domain_brute_type": "test"},
        "ip_config": {
            "port_scan": True,
            "port_scan_type": "top100",
            "service_detection": False,
            "host_timeout": 0,
            "port_parallelism": 32,
            "port_min_rate": 60,
        },
        "site_config": {"site_identify": False, "site_capture": False},
        "file_leak": False,
        "npoc_service_detection": False,
        "scope_config": {"scope_id": "scope"},
        "poc_config": [],
        "brute_config": [],
    }

    item = {"name": "test", "desc": "old", "policy": policy}

    patch = {
        "name": "update-name",
        "desc": "test",
        "policy": {
            "domain_config": {"domain_brute_type": "big"},
            "site_config": {"site_identify": True, "web_info_hunter": True, "not_exist": True},
        },
    }

    allow_keys = gen_model_policy_keys(add_policy_fields["policy"]) + ["name", "desc", "policy"]
    updated = change_policy_dict(item, patch, allow_keys)

    assert updated["name"] == "update-name"
    assert updated["desc"] == "test"
    assert updated["policy"]["site_config"]["site_identify"] is True
    assert updated["policy"]["site_config"]["web_info_hunter"] is True
    assert "not_exist" not in updated["policy"]["site_config"]
