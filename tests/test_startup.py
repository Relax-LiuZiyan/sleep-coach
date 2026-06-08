from pathlib import Path

from sleep_coach.system import build_startup_command


def test_build_startup_command_uses_script_for_source_python_run():
    command = build_startup_command(
        executable_path=Path(r"C:\Python314\python.exe"),
        working_directory=Path(r"D:\sleep"),
        frozen=False,
    )

    assert 'cd /d "D:\\sleep"' in command
    assert 'start "" "C:\\Python314\\pythonw.exe" "D:\\sleep\\launch_sleep_coach.pyw" --background' in command


def test_build_startup_command_uses_executable_for_frozen_build():
    command = build_startup_command(
        executable_path=Path(r"C:\Program Files\Sleep Coach\SleepCoach.exe"),
        working_directory=Path(r"C:\Program Files\Sleep Coach"),
        frozen=True,
    )

    assert 'cd /d "C:\\Program Files\\Sleep Coach"' in command
    assert 'start "" "C:\\Program Files\\Sleep Coach\\SleepCoach.exe" --background' in command
    assert "run.py" not in command
