import pytest

from app.utils import is_valid_exclude_ports


@pytest.mark.parametrize(
    "expression, expected",
    [
        ("80", True),
        ("80,443", True),
        ("8080-8089", True),
        ("80,443,8080-8089", True),
        ("8089-8080", False),
        ("80,70000", False),
        ("80,http", False),
        ("", False),
        ("abc-def", False),
        ("80-1-2,", False),
    ],
)
def test_is_valid_exclude_ports(expression, expected):
    assert is_valid_exclude_ports(expression) is expected
