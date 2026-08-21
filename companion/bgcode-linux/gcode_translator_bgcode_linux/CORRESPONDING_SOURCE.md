# Corresponding Source (AGPL-3.0 §6) — bgcode (Linux)

This file ships **inside** the package (and therefore inside the built wheel) so the
AGPL-3.0 Corresponding Source travels with the binary regardless of how the package is
distributed.

The binary is a **clean, unmodified** build of the upstream libbgcode project — neither the
source code nor the build scripts were changed — so the Corresponding Source is simply the
upstream tree at the commit below, built with the stock CMake presets.

## Binary identity

| Field | Value |
|-------|-------|
| Binary SHA-256 | `15c6fe4d54defc4d375524452f433ff3f4e7a10e3b23f89c14096cd5484c1f4b` |
| Binary size | 181528 bytes |
| Format | ELF 64-bit x86-64, dynamically linked, GNU/Linux |
| Repository | https://github.com/prusa3d/libbgcode |
| Version | libbgcode 0.2.0 |
| Commit | `5041c093b33e2748e76d6b326f2251310823f3df` (branch `main`, 2025-02-20) |
| Source code modifications | none (clean upstream checkout) |
| Build-script modifications | none |

## Build environment

| Field | Value |
|-------|-------|
| Target | ELF 64-bit x86-64, dynamically linked, GNU/Linux |
| Toolchain | GNU g++ 11.4.0 |
| Build system | CMake 3.22.1 |
| Build type | Release |
| Configure/build | CMake preset `default` (deps preset `default`) |

## Reproduce

```bash
# Clean checkout of the exact upstream commit
git clone https://github.com/prusa3d/libbgcode
cd libbgcode
git checkout 5041c093b33e2748e76d6b326f2251310823f3df

# Configure + build with the stock presets (no patches needed)
cmake --preset default        # configures deps + project (Release)
cmake --build --preset default

# Result (verify against the SHA-256 above):
#    build-default/src/LibBGCode/cmd/bgcode
```

## Written Offer

The Corresponding Source for the exact version above is publicly available at the commit
link. In addition, for at least three (3) years from the date of distribution, the author
will provide, on request, a copy of the complete Corresponding Source of this binary.
Contact: david.herrmann@kit.edu
