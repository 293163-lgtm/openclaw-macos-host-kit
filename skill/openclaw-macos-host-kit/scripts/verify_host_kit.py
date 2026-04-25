#!/usr/bin/env python3
import json
import os
import pathlib
import shutil
import subprocess
import sys


def run(cmd: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(cmd, text=True, capture_output=True)
    return p.returncode, p.stdout, p.stderr


def main() -> int:
    openclaw = shutil.which('openclaw') or '/opt/homebrew/bin/openclaw'
    result = {
        'os': None,
        'openclaw_bin': openclaw,
        'checks': {}
    }

    code, out, err = run(['uname', '-s'])
    result['os'] = out.strip() if code == 0 else None

    code, out, err = run([openclaw, 'status', '--deep'])
    result['checks']['openclaw_status'] = {
        'ok': code == 0,
        'contains_dashboard': 'Dashboard' in out,
        'sample': '\n'.join(out.splitlines()[:20]) if out else err[:800]
    }

    code, out, err = run(['osascript', '-e', 'tell application "System Events" to get name of every process'])
    result['checks']['osascript_system_events'] = {
        'ok': code == 0,
        'note': 'Basic AppleScript / System Events reachability only; not a full Accessibility grant proof.',
        'sample': out[:500] if out else err[:500]
    }

    desktop = pathlib.Path.home() / 'Desktop'
    expected = [
        'OpenClaw Host.command',
        'OpenClaw权限收口.command',
        'OpenClaw 工作台',
    ]
    existing = []
    for name in expected:
        p = desktop / name
        existing.append({'name': name, 'exists': p.exists(), 'path': str(p)})
    result['checks']['desktop_artifacts'] = existing

    code, out, err = run([openclaw, 'system', 'heartbeat', 'last'])
    result['checks']['heartbeat_last'] = {
        'ok': code == 0,
        'sample': out[:500] if out else err[:500]
    }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
