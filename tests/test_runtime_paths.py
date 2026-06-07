from pathlib import Path

from sleep_coach.runtime import app_icon_path, resource_root


def test_resource_root_uses_source_tree_when_not_frozen(monkeypatch):
    fake_runtime = Path(r"D:\sleep")

    monkeypatch.setattr("sleep_coach.runtime.is_frozen", lambda: False)
    monkeypatch.setattr("sleep_coach.runtime.source_root", lambda: fake_runtime)

    assert resource_root() == fake_runtime


def test_app_icon_path_uses_meipass_when_frozen(monkeypatch):
    fake_meipass = Path(r"C:\bundle\_internal")

    monkeypatch.setattr("sleep_coach.runtime.is_frozen", lambda: True)
    monkeypatch.setattr("sleep_coach.runtime.bundle_root", lambda: fake_meipass)

    assert app_icon_path() == fake_meipass / "sleep_coach" / "assets" / "sleep_coach.ico"
