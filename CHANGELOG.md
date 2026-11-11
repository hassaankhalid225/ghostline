# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [1.1.0] — 2026-11-12

### Changed
- New name and logo: **Caption Assist is now Ghostline** — a ghost (invisible on screen shares)
  whose eyes are two caption lines. New app icon, tray icon, window title and README logo.
- Opening the AI side panel keeps the window's size instead of enlarging it.

### Added
- **Send** now presses the chat's send button for you, so the answer appears right away
  (turn off in the arrow menu), with an optional instruction sent before the captions.

### Fixed
- Sign-in pop-ups from the AI panel open above the always-on-top window instead of behind it.

### Upgrading
- Settings, AI panel sign-ins and transcripts from Caption Assist move over automatically on
  first start.

## [1.0.0] — 2026-11-12

First release (as Caption Assist), built on Live Caption Recorder 1.0.0.

### Added
- AI side panel: ChatGPT, Claude or any website in a split view next to the captions (Ctrl+B).
- Send captions to the AI chat box (Ctrl+Enter): new since last send, last 5 sentences or all.
- Private mode now covers every window of the app (menus, tooltips, pop-ups) and is on by default.

## [Live Caption Recorder 1.0.0] — 2026-11-11

### Added
- Persistent, de-duplicated transcript built from Windows Live Captions.
- Recording continues while minimized (Live Captions is parked off-screen, restored on exit).
- Copy all, save/export as text, text with timestamps, Markdown and SRT.
- Auto-save of each session to `Documents\Live Caption Recorder`.
- Frosted-glass caption bar with compact/expanded modes, adjustable font size, always-on-top.
- Optional private mode (hidden from screen capture) with real background blur.
- System tray icon, single-instance guard, rotating log file, crash dialog.
- Automatic recovery when Live Captions stops responding.
- Unit tests, ruff lint, GitHub Actions CI and PyInstaller release build.
