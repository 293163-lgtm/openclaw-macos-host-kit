# Preflight

Before installing the host kit on a Mac, verify:

1. macOS host confirmed
2. `openclaw` CLI exists in PATH or known install path
3. target home directory confirmed
4. workspace root confirmed
5. desktop path confirmed
6. current OpenClaw service mode known
7. whether old desktop artifacts already exist
8. whether `.app` creation tool (`osacompile`) exists
9. whether the user wants desktop-root duplicate entries or package-only entries
10. whether heartbeat cadence should stay `30m` or use a custom value

## Minimal evidence commands

```bash
command -v openclaw
openclaw status --deep
command -v osacompile
ls -la ~/Desktop
```

## If migrating from old setup
- inspect existing desktop package first
- do not delete old entry before validating new one
- preserve or map useful grouped shortcuts into the new package
