# Releasing

How to cut a versioned, reproducible release of `gcode-translator` and its
platform companion package(s).

## Versioning model

This project is **git-only** (not published to PyPI). The `bgcode` binary ships
as a separate companion package under `companion/`, pulled in via the
`[linux]` / `[windows]` / `[macos]` extras. Each extra is a **git direct
reference** in `pyproject.toml`, e.g.:

```
gcode-translator-bgcode-linux @ git+https://github.com/herrdivad/GCode_Translator.git#subdirectory=companion/bgcode-linux ; sys_platform == 'linux'
```

With no ref, that URL tracks the default branch (`master`) — fine for "install
latest", but **not reproducible**. A release pins the ref to a tag so the base
package and its companion always come from the *same* commit.

> **The self-reference is intentional and valid.** The `pyproject.toml` inside
> tag `vX.Y.Z` points its extra URLs at `@vX.Y.Z`. A git tag is just a pointer,
> and the URL is only resolved at install time — so you create the release
> commit first, then tag it, and everything is internally consistent.

## Release checklist

For a release `vX.Y.Z` (replace `X.Y.Z` everywhere below):

1. **Bump versions**
   - `pyproject.toml` → `version = "X.Y.Z"`
   - `companion/bgcode-linux/pyproject.toml` → bump only if the binary changed
     (new libbgcode build); otherwise leave as-is. See "Companion version" below.

2. **Pin the extra URLs to the tag** in `pyproject.toml`. Add `@vX.Y.Z`
   *before* the `#subdirectory` fragment in **every** extra (`linux`, `windows`,
   `macos`) — including the ones whose companion does not exist yet:

   ```
   ... GCode_Translator.git@vX.Y.Z#subdirectory=companion/bgcode-linux ; sys_platform == 'linux'
   ```

   > ⚠️ **This step is what makes the release reproducible — do not skip it.**
   > An unpinned URL inside a tagged commit silently resolves to whatever is on
   > `master` at install time, so two people installing "the same" tag can end up
   > with different companion binaries. Check afterwards that no unpinned URL is
   > left:
   >
   > ```bash
   > grep -n 'GCode_Translator.git#' pyproject.toml   # must print nothing
   > ```

3. **Clean stale build artifacts and run the tests** (must be green):

   ```bash
   rm -rf build gcode_translator.egg-info UNKNOWN.egg-info
   pip install -e ".[dev]"
   pytest
   ```

4. **Commit, tag, push** (tag the release commit itself):

   ```bash
   git add pyproject.toml companion/bgcode-linux/pyproject.toml
   git commit -m "release vX.Y.Z"
   git tag vX.Y.Z
   git push origin master --follow-tags
   ```

5. **(Optional) GitHub Release.** Create a Release from tag `vX.Y.Z` with a
   changelog. Not required for installation — `git+...@vX.Y.Z` is enough.

## Verify the release (in a clean venv)

```bash
python3 -m venv /tmp/verify-release && source /tmp/verify-release/bin/activate
python -m pip install --upgrade pip

# base only (binary-free):
pip install "git+https://github.com/herrdivad/GCode_Translator.git@vX.Y.Z"

# with the Linux companion (pulled from the SAME tag automatically):
pip install "gcode-translator[linux] @ git+https://github.com/herrdivad/GCode_Translator.git@vX.Y.Z"

pip list | grep -i gcode   # expect gcode-translator (+ gcode-translator-bgcode-linux for the extra)
deactivate
```

## What users install

```bash
# latest (tracks master, not reproducible):
pip install "gcode-translator[linux] @ git+https://github.com/herrdivad/GCode_Translator.git"

# pinned release (reproducible):
pip install "gcode-translator[linux] @ git+https://github.com/herrdivad/GCode_Translator.git@vX.Y.Z"
```

## Notes

- **Companion version.** The companion is resolved by **URL + ref**, not by a
  version specifier, so pip installs whatever is in the subdirectory at that tag
  regardless of its version number. Its version in
  `companion/bgcode-linux/pyproject.toml` is therefore informational — bump it
  only when the shipped binary actually changes (e.g. a new libbgcode build),
  and record the new Corresponding Source details in
  `companion/bgcode-linux/README.md`.
- **Placeholder extras.** As of `v1.2.0` the Linux *and* Windows companions
  exist (`companion/bgcode-linux/`, `companion/bgcode-windows/`); only `[macos]`
  still points at a directory that has not been added yet. Pinning its URL to the
  tag is harmless: it only resolves if someone requests that extra on that
  platform, which fails cleanly until the companion is added.
- **After tagging, keep `master` moving.** New work on `master` can leave the
  extra URLs pinned to the last tag or reset them to unpinned (tracking
  `master`) — just re-pin them at the next release. This project keeps them
  **pinned**, so a fresh clone of `master` always installs a known-good
  companion. Whatever you choose, the pinned tag stays
  reproducible because its commit is frozen.
```
