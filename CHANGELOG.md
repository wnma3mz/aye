# Changelog

## 0.0.5 - 2026-05-01

- Generalize menu detection to support numbered, lettered, bulleted, cursor-prefixed, and plain `Yes`/`No` choice lines.
- Add Codex file-edit and generic plain-choice end-to-end prompt tests.
- Restore `--fifo` as an explicit advanced input channel.
- Run CI tests across Python 3.10, 3.11, and 3.12.
- Improve packaged updater replacement to use a staging file and atomic rename.

## 0.0.4 - 2026-05-01

- Improve Claude-style menu detection across ANSI, cursor, numbered, and described choice formats.
- Send carriage return for menu selections so TUI prompts receive a real Enter key.
- Scope dangerous-command blocking to the current `Bash(...)` command, preventing `rm` prompts while allowing later safe commands.
- Keep Aye diagnostic logs quiet by default and expose them through `--verbose`.
- Add end-to-end tests for menu confirmation, dangerous command blocking, and quiet logging.

## 0.0.3 - 2026-05-01

- Bundle trusted CA certificates for `aye update` in packaged macOS binaries.

## 0.0.2 - 2026-05-01

- Add `aye --version`.
- Add `aye update` for updating installed release binaries.
- Include the release tag in archive names, such as `aye-v0.0.2-darwin-arm64.tar.gz`.

## 0.0.1 - 2026-05-01

- Initial release of `aye`.
- Wrap Claude Code, Gemini CLI, Codex, or another interactive CLI in the same terminal.
- Auto-confirm explicit `yes`, `y`, and menu-style confirmation prompts.
- Block auto-confirmation when recent output includes `rm`, `rmdir`, or `unlink`.
- Provide Linux and macOS release builds through GitHub Releases.
