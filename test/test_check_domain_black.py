from app.utils import check_domain_black, is_valid_domain


def test_black_domain_matches_wildcard():
    assert check_domain_black("test.wire.comm.example.com")
    assert not check_domain_black("test.wire1.comm.example.com")


def test_is_valid_domain_rejects_prefix_exclamation():
    assert not is_valid_domain("!test.test.example.com")
