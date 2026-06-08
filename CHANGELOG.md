# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [0.1.3] - 2026-06-08

### Changed

- Default launch now runs in background mode and only shows the main window when `--show` is passed.
- Startup launch now uses `launch_sleep_coach.pyw --background`, so login startup no longer pushes the main window to the foreground.
- During warning, overtime, fullscreen, and penalty stages, the top bar is forced on top and raised to the front more reliably.
- Windows installer version is now resolved automatically from the release tag or `SLEEP_COACH_VERSION`, with a development fallback for local builds.

- Main window now hides to the system tray when minimized or closed, so background running behaves more consistently on Windows.

## [0.1.2] - 2026-06-07

### Changed

## [0.1.1] - 2026-06-07

### Added

- PyInstaller build spec for Windows desktop packaging
- Inno Setup installer script
- PowerShell build script for generating `SleepCoach-Setup.exe`
- GitHub Actions workflow for building and publishing Windows release assets

## [0.1.0] - 2026-06-07

### Added

- Initial public project documentation
- MIT license
- Contribution guide
- Code of conduct
- Changelog
