# NewzDeck v3.5.33 source status

v3.5.33 is NewzDeck's first **source-complete Windows production release**.

Every NewzDeck-owned Windows executable in the v3.5.33 Portable/Setup payload maps to buildable source in `src/windows/`. The Python backend, SAB adapter, Automation engine, and browser UI are also present directly as source under `src/app/`.

The legacy `NewzDeckBootstrap.exe` and `NewzDeckCore.exe` binaries are retired and are not shipped by v3.5.33.

Canonical source-to-Portable build:

```text
python release/windows/build-portable.py --version 3.5.33 --output NewzDeck_v3.5.33_Portable.zip
```

Canonical toolchain:

- Python 3.12.10
- Go 1.23.2
- GOOS=windows
- GOARCH=amd64
- CGO_ENABLED=0
- Inno Setup 7.1.0 x64 for Setup.exe

The final Windows acceptance r5 Portable ZIP used during pre-publication validation had SHA-256:

```text
6b96d0cd8ea92a29e5178d33eea1208de0309c70cf0b3e6e04d40ebf65cc2e39
```

The final published v3.5.33 Portable asset has SHA-256:

```text
a2e7ec5a79904f40e5fb0b864ee420c002b591e01aa64b840b58b026eed90935
```

v3.5.33 completed the source-publication transition and is now the production release. The r5 value is retained as historical acceptance provenance; the published hash is the integrity value for the Portable asset distributed from the GitHub Release.

See `SOURCE_STATUS.json` for the source map/hashes and `docs/RELEASE_COMPLIANCE.md` for the publication gate.
