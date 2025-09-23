from app.services.nuclei_scan import NucleiScan, nuclei_scan


def test_nuclei_scan_returns_empty_without_binary(monkeypatch):
    monkeypatch.setattr("app.services.nuclei_scan.NucleiScan.check_have_nuclei", lambda self: False)

    assert nuclei_scan(["https://demo"] ) == []


def test_nuclei_scan_runs_with_stubs(monkeypatch):
    steps = {}

    monkeypatch.setattr("app.services.nuclei_scan.NucleiScan.check_have_nuclei", lambda self: True)

    def fake_check_flag(self):
        self.nuclei_json_flag = "-json"
        steps["flag"] = True

    monkeypatch.setattr("app.services.nuclei_scan.NucleiScan._check_json_flag", fake_check_flag)
    monkeypatch.setattr("app.services.nuclei_scan.NucleiScan.exec_nuclei", lambda self: steps.setdefault("exec", True))
    monkeypatch.setattr("app.services.nuclei_scan.NucleiScan.dump_result", lambda self: ["result"])
    monkeypatch.setattr("app.services.nuclei_scan.NucleiScan._delete_file", lambda self: steps.setdefault("deleted", True))

    scan = NucleiScan(["https://demo"])
    result = scan.run()

    assert result == ["result"]
    assert steps == {"flag": True, "exec": True, "deleted": True}
