import pytest

from app.services import expr


@pytest.mark.parametrize(
    "expression, expected",
    [
        ('ab = "abc"', False),
        ('!(body == "jeecms" && body == "http://wwwjeecms.com") && body != "powered by"', True),
        ('(title == "jeecms" && body="http://wwwjeecms.com") || header = "powered by jeecms"', True),
        ('(title=="jeecms"&&body="http://wwwjeecms.com")||header="powered by jeecms"', True),
    ],
)
def test_check_expression(expression, expected):
    assert expr.check_expression(expression) == expected


@pytest.mark.parametrize(
    "expression, expected",
    [
        ('icon_hash == "116323821"', True),
        ('body = "test" && icon_hash == "116323821"', True),
        ('body = "test" || icon_hash == "11111111"', True),
        ('body = "test3" && icon_hash == "11111111"', False),
        ('!(body = "test3" && icon_hash == "11111111")', True),
        ('header == "header test2"', True),
        ('body == "body test1" || icon_hash = "116323821"', True),
        ('title = "title \\" test3"', True),
        ('title == "title \\" test3"', True),
        ('title = " \\" "', True),
        ('icon_hash != "11111111"', True),
        ('body != "test" && icon_hash != "116323821"', False),
        ('body="test"&&icon_hash=="116323821"', True),
        ('body="test"&&body!="<"', False),
        ('body=="body test1<"', True),
        ('body="body test1<"', True),
        ('body="test"&&body="<"', True),
        ('!(body="test")', False),
        ('!body="test"', False),
    ],
)
def test_evaluate_expression(expression, expected):
    variables = {
        'body': "body test1<",
        'header': "header test2",
        'title': "title \" test3",
        'icon_hash': "116323821",
    }

    assert expr.evaluate(expression, variables) == expected


def test_parse_and_evaluate_share_same_result():
    expression = 'body = "body_test" && status_code == "200" && header = "header" && title = "title \\""'
    variables = {
        'body': "body" * 1024 * 2 + "_test",
        'header': "header test2",
        'title': "title \" test3",
        'icon_hash': "116323821",
    }

    parsed = expr.parse_expression(expression)

    assert expr.evaluate(expression, variables) == expr.evaluate_expression(parsed, variables)

