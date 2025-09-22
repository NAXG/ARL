from app.services.githubSearch import GithubResult, github_search_code


def make_item():
    return {
        "git_url": "https://api.github.com/repos/demo/repo/git/blobs/1",
        "html_url": "https://github.com/demo/repo/blob/main/file.txt",
        "repository": {"full_name": "demo/repo"},
        "path": "file.txt",
    }


def test_github_result_commit_date_cached(monkeypatch):
    calls = []

    def fake_github_client(url, params=None, cnt=0):
        calls.append((url, tuple(sorted((params or {}).items()))))
        assert url.endswith("/commits")
        return [{"commit": {"author": {"date": "2024-01-01T00:00:00Z"}}}]

    monkeypatch.setattr("app.services.githubSearch.github_client", fake_github_client)

    result = GithubResult(make_item())
    assert result.commit_date == "2024-01-01 08:00:00"
    assert result.commit_date == "2024-01-01 08:00:00"
    assert len(calls) == 1


def test_github_search_code_wraps_items(monkeypatch):
    def fake_github_client(url, params=None, cnt=0):
        return {
            "total_count": 2,
            "items": [make_item(), make_item()],
        }

    monkeypatch.setattr("app.services.githubSearch.github_client", fake_github_client)

    results, total = github_search_code("query", per_page=1, page=1)

    assert total == 2
    assert len(results) == 2
    assert all(isinstance(r, GithubResult) for r in results)
