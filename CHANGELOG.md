# Changelog

All notable changes to this project are documented here. This project is
git-only (not published to PyPI); a "release" is a git tag plus an optional
GitHub Release. See [RELEASING.md](./RELEASING.md).

## [v1.2.0] — 2026-08-24

First release of the **companion-package architecture** (PR #1, issue #2).

### Changed
- **The `bgcode` binary no longer ships in the base package.** `gcode-translator`
  is now MIT-only and binary-free. The AGPL-3.0 `bgcode` binaries live in
  separate, opt-in companion packages under `companion/`, installed via the
  `[linux]` / `[windows]` / `[macos]` extras.
- Extra URLs are **pinned to `@v1.2.0`**, so the base package and its companion
  always resolve to the same commit — an install of this tag is reproducible.

### Added
- `companion/bgcode-linux/` — package `gcode-translator-bgcode-linux`, extra `[linux]`.
- `companion/bgcode-windows/` — package `gcode-translator-bgcode-windows`, extra
  `[windows]`; self-contained `/MT` build, needs no VC++ Redistributable.
- Each companion carries the full AGPL-3.0 license text and its own
  `CORRESPONDING_SOURCE.md` (upstream commit, build environment, and — for
  Windows — the dependency build-script patch), so a built wheel is
  self-contained for AGPL compliance.
- **Platform Support** table in `README.md`.
- `.gitattributes` — the repository stores and checks out LF everywhere, so a
  Windows IDE and WSL/git no longer disagree about line endings.

### Not yet available
- **macOS.** The `[macos]` extra exists but points at a companion directory that
  has not been added yet; requesting it on darwin fails at install time. Use the
  base package on macOS — everything except `.bgcode` decoding works.

### Upgrade notes
Installing the base package alone no longer gives you `.bgcode` support. Add the
extra for your platform:

```bash
pip install "gcode-translator[linux] @ git+https://github.com/herrdivad/GCode_Translator.git@v1.2.0"
```

Without a companion, `.bgcode` conversion fails with a message naming the extra
to install; `.gcode` / `.gx` handling is unaffected.

## [v1.1.0] and earlier

See the [GitHub Releases](https://github.com/herrdivad/GCode_Translator/releases)
page. Those tags predate the companion split and bundle the `bgcode` binary
inside the base package.
