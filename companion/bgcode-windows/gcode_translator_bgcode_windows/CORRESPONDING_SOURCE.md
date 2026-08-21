# Corresponding Source (AGPL-3.0 §6) — bgcode.exe

This file ships **inside** the package (and therefore inside the built wheel) so the
AGPL-3.0 Corresponding Source travels with the binary regardless of how the package is
distributed. Under AGPL-3.0 the Corresponding Source is the program's source code **plus
the scripts used to control its compilation and installation** — hence the build-script
patch shipped alongside this file (`0001-deps-static-crt-and-policy-floor.patch`) is part
of it.

The libbgcode **source code is unmodified**; only the dependency build scripts were
patched (see below).

## Binary identity

| Field | Value |
|-------|-------|
| Binary SHA-256 | `49dfc4b5b698a455d4eaa56a91d745ba5ac0aad641643077286b945a6ae43927` |
| Binary size | 427008 bytes |
| Format | PE32+ executable (console) x86-64 |
| Repository | https://github.com/prusa3d/libbgcode |
| Version | libbgcode 0.2.0 |
| Commit | `5041c093b33e2748e76d6b326f2251310823f3df` (branch `main`, 2025-02-20) |
| Source code modifications | none (clean upstream checkout of `src/`) |
| Build-script modifications | `0001-deps-static-crt-and-policy-floor.patch` (dependency build config only) |

## Build environment

| Field | Value |
|-------|-------|
| Toolchain | Visual Studio Community 2026 (v18.7.0), MSVC toolset 14.51.36231 (cl 19.51.36247), x64 |
| Build system | CMake 4.3.1-msvc1 (VS-bundled) + Ninja 1.13.2 |
| Windows SDK | 10.0.26100.0 |
| MSVC runtime | static (`/MT`, via `CMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded`) |
| Build type | Release |

## Build-script modifications

Two changes to the dependency superbuild (`deps/CMakeLists.txt`), captured in the shipped
patch. They affect only *how* the unmodified code is compiled, not its behavior:

1. **CMake policy floor.** VS 2026 ships CMake 4.x, which dropped compatibility with the
   very old `cmake_minimum_required()` declared by a vendored dependency (ZLIB). Passing
   `-DCMAKE_POLICY_VERSION_MINIMUM=3.5` to the dependency sub-builds lets them configure.

2. **Static MSVC runtime (`/MT`).** By default the superbuild forwards `/MD` (dynamic
   runtime) to every dependency. Setting policy `CMP0091=NEW` **before** `project()` (so the
   forwarded `CMAKE_<LANG>_FLAGS_RELEASE` carry no `/MD`) plus
   `CMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded` for each dependency makes the whole stack —
   including Boost 1.82, built here via CMake, not b2 — link the static CRT. The result
   depends only on `KERNEL32.dll`.

## Reproduce

```bash
# 1) Clean checkout of the exact upstream commit
git clone https://github.com/prusa3d/libbgcode
cd libbgcode
git checkout 5041c093b33e2748e76d6b326f2251310823f3df

# 2) Apply the build-script patch shipped next to this file
git apply /path/to/0001-deps-static-crt-and-policy-floor.patch

# 3) Configure + build with the native MSVC toolchain (VS x64 dev prompt, or from WSL by
#    first `call`-ing VsDevCmd.bat -arch=amd64 inside a cmd.exe session)
cmake --preset default -G Ninja -DLibBGCode_BUILD_DEPS=ON ^
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 ^
  -DCMAKE_POLICY_DEFAULT_CMP0091=NEW ^
  -DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded
cmake --build --preset default

# 4) Result (verify against the SHA-256 above):
#    build-default/src/LibBGCode/cmd/bgcode.exe
# Confirm it is standalone (only KERNEL32.dll should appear):
#    dumpbin /dependents build-default/src/LibBGCode/cmd/bgcode.exe
```

## Written Offer

The Corresponding Source for the exact version above — the upstream source at the commit
link plus the build-script patch shipped next to this file — is provided here. In addition,
for at least three (3) years from the date of distribution, the author will provide, on
request, a copy of the complete Corresponding Source of this binary.
Contact: david.herrmann@kit.edu
