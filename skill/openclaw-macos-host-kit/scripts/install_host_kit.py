#!/usr/bin/env python3
import argparse
import json
import os
import pathlib
import shlex
import shutil
import subprocess
import sys
import textwrap
from typing import Any


def run(cmd: list[str], check: bool = True, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, text=True, capture_output=capture)


class Installer:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.actions: list[dict[str, Any]] = []

    def record(self, action: str, **data: Any) -> None:
        self.actions.append({"action": action, **data})

    def write_file(self, path: pathlib.Path, content: str, mode: int | None = None) -> None:
        self.record("write_file", path=str(path), mode=oct(mode) if mode is not None else None)
        if self.dry_run:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        if mode is not None:
            path.chmod(mode)

    def mkdir(self, path: pathlib.Path) -> None:
        self.record("mkdir", path=str(path))
        if self.dry_run:
            return
        path.mkdir(parents=True, exist_ok=True)

    def symlink_force(self, target: pathlib.Path, link: pathlib.Path) -> None:
        self.record("symlink", target=str(target), link=str(link))
        if self.dry_run:
            return
        if link.exists() or link.is_symlink():
            if link.is_dir() and not link.is_symlink():
                shutil.rmtree(link)
            else:
                link.unlink()
        os.symlink(str(target), str(link))

    def copy2(self, src: pathlib.Path, dst: pathlib.Path) -> None:
        self.record("copy", src=str(src), dst=str(dst))
        if self.dry_run:
            return
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    def unlink(self, path: pathlib.Path) -> None:
        self.record("unlink", path=str(path))
        if self.dry_run:
            return
        path.unlink(missing_ok=True)

    def rmtree(self, path: pathlib.Path) -> None:
        self.record("rmtree", path=str(path))
        if self.dry_run:
            return
        if path.exists():
            shutil.rmtree(path)

    def move(self, src: pathlib.Path, dst: pathlib.Path) -> None:
        self.record("move", src=str(src), dst=str(dst))
        if self.dry_run:
            return
        dst.parent.mkdir(parents=True, exist_ok=True)
        if src.exists():
            shutil.move(str(src), str(dst))


def patch_heartbeat(config_path: pathlib.Path, every: str, target: str = "none") -> None:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    agents = cfg.get("agents") or {}
    defaults = agents.get("defaults") or {}
    hb = defaults.get("heartbeat") or {}
    hb["every"] = every
    hb["target"] = target
    defaults["heartbeat"] = hb
    agents["defaults"] = defaults
    cfg["agents"] = agents
    config_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def archive_existing_worktable(inst: Installer, desktop: pathlib.Path, old_name: str, archive_root_name: str = "OpenClaw旧入口归档") -> pathlib.Path | None:
    if not old_name:
        return None
    src = desktop / old_name
    if not src.exists():
        inst.record("archive_skip_missing", path=str(src))
        return None
    import datetime
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dst = desktop / archive_root_name / f"{old_name}-{stamp}"
    inst.move(src, dst)
    return dst


def build_host_scripts(inst: Installer, home: pathlib.Path, host_env_path: pathlib.Path, gateway_port: int) -> tuple[pathlib.Path, pathlib.Path]:
    bin_dir = home / "bin"
    host_sh = bin_dir / "openclaw-host.sh"
    stop_sh = bin_dir / "openclaw-host-stop.sh"
    host_sh_text = textwrap.dedent(f'''\
        #!/bin/zsh
        set -euo pipefail
        source {shlex.quote(str(host_env_path))}
        LABEL="ai.openclaw.gateway"
        PLIST="$HOME/Library/LaunchAgents/${{LABEL}}.plist"
        PORT="{gateway_port}"
        UIDN=$(id -u)
        echo "[host] OpenClaw Terminal host starting on port $PORT"
        if [ -f "$PLIST" ]; then
          launchctl bootout gui/$UIDN "$PLIST" 2>/dev/null || true
          launchctl disable gui/$UIDN/$LABEL 2>/dev/null || true
        fi
        if lsof -nP -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1; then
          echo "[host] port $PORT already in use; existing listener:"
          lsof -nP -iTCP:$PORT -sTCP:LISTEN || true
          exit 1
        fi
        cd "$HOME"
        exec /opt/homebrew/bin/node /opt/homebrew/lib/node_modules/openclaw/dist/index.js gateway --port "$PORT"
    ''')
    stop_sh_text = textwrap.dedent('''\
        #!/bin/zsh
        set -euo pipefail
        LABEL="ai.openclaw.gateway"
        PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
        UIDN=$(id -u)
        pkill -f '/opt/homebrew/lib/node_modules/openclaw/dist/index.js gateway --port' 2>/dev/null || true
        if [ -f "$PLIST" ]; then
          launchctl enable gui/$UIDN/$LABEL 2>/dev/null || true
          launchctl bootstrap gui/$UIDN "$PLIST" 2>/dev/null || true
        fi
        echo "[host] stopped Terminal-hosted gateway and re-enabled LaunchAgent"
    ''')
    inst.write_file(host_sh, host_sh_text, 0o755)
    inst.write_file(stop_sh, stop_sh_text, 0o755)
    return host_sh, stop_sh


def build_host_env(inst: Installer, host_env: pathlib.Path, home: pathlib.Path, gateway_port: int) -> pathlib.Path:
    if host_env.exists():
        return host_env
    content = textwrap.dedent(f'''\
        #!/bin/zsh
        set -euo pipefail
        export HOME={json.dumps(str(home))}
        export PATH='/opt/homebrew/opt/node/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin'
        export OPENCLAW_GATEWAY_PORT={json.dumps(str(gateway_port))}
        [[ -f ~/.zprofile ]] && source ~/.zprofile >/dev/null 2>&1 || true
        [[ -f ~/.zshrc ]] && source ~/.zshrc >/dev/null 2>&1 || true
    ''')
    inst.write_file(host_env, content, 0o755)
    return host_env


def build_host_command(inst: Installer, desktop: pathlib.Path, host_sh: pathlib.Path) -> pathlib.Path:
    path = desktop / "OpenClaw Host.command"
    inst.write_file(path, f"#!/bin/zsh\nexec {shlex.quote(str(host_sh))}\n", 0o755)
    return path


def build_restore_command(inst: Installer, desktop: pathlib.Path, stop_sh: pathlib.Path) -> pathlib.Path:
    path = desktop / "恢复OpenClaw后台服务.command"
    inst.write_file(path, f"#!/bin/zsh\nexec {shlex.quote(str(stop_sh))}\n", 0o755)
    return path


def build_permissions_command(inst: Installer, desktop: pathlib.Path) -> pathlib.Path:
    path = desktop / "OpenClaw权限收口.command"
    text = textwrap.dedent('''\
        #!/bin/zsh
        open 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'
        sleep 1
        open 'x-apple.systempreferences:com.apple.preference.security?Privacy_ScreenCapture'
        sleep 1
        open 'x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles'
    ''')
    inst.write_file(path, text, 0o755)
    return path


def build_heartbeat_commands(inst: Installer, desktop: pathlib.Path, config_path: pathlib.Path, cadence: str,
                             openclaw_bin: str,
                             off_name: str = "OpenClaw-专注模式（关闭自动心跳）.command",
                             on_name: str = "OpenClaw-恢复自动心跳.command") -> tuple[pathlib.Path, pathlib.Path]:
    off = desktop / off_name
    on = desktop / on_name
    off_lines = [
        "#!/bin/zsh",
        "set -euo pipefail",
        'export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"',
        "python3 - <<'PY'",
        "import json, pathlib",
        f"p = pathlib.Path({json.dumps(str(config_path))})",
        "c = json.loads(p.read_text())",
        "agents = c.get('agents') or {}",
        "defaults = agents.get('defaults') or {}",
        "hb = defaults.get('heartbeat') or {}",
        "hb['every'] = ''",
        "hb['target'] = 'none'",
        "defaults['heartbeat'] = hb",
        "agents['defaults'] = defaults",
        "c['agents'] = agents",
        "p.write_text(json.dumps(c, ensure_ascii=False, indent=2) + '\\n')",
        "print('CONFIG_HEARTBEAT', defaults['heartbeat'])",
        "PY",
        f"{shlex.quote(openclaw_bin)} system heartbeat disable",
        'printf "\\n=== STATUS ===\\n"',
        f"{shlex.quote(openclaw_bin)} status --deep | sed -n '1,40p'",
        'printf "\\n已关闭自动心跳。按回车关闭窗口。"',
        "read _",
    ]
    on_lines = [
        "#!/bin/zsh",
        "set -euo pipefail",
        'export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"',
        "python3 - <<'PY'",
        "import json, pathlib",
        f"p = pathlib.Path({json.dumps(str(config_path))})",
        "c = json.loads(p.read_text())",
        "agents = c.get('agents') or {}",
        "defaults = agents.get('defaults') or {}",
        "hb = defaults.get('heartbeat') or {}",
        f"hb['every'] = {json.dumps(cadence)}",
        "hb['target'] = 'none'",
        "defaults['heartbeat'] = hb",
        "agents['defaults'] = defaults",
        "c['agents'] = agents",
        "p.write_text(json.dumps(c, ensure_ascii=False, indent=2) + '\\n')",
        "print('CONFIG_HEARTBEAT', defaults['heartbeat'])",
        "PY",
        f"{shlex.quote(openclaw_bin)} system heartbeat enable",
        'printf "\\n=== STATUS ===\\n"',
        f"{shlex.quote(openclaw_bin)} status --deep | sed -n '1,40p'",
        f'printf "\\n已恢复自动心跳（{cadence}）。按回车关闭窗口。"',
        "read _",
    ]
    off_text = "\n".join(off_lines) + "\n"
    on_text = "\n".join(on_lines) + "\n"
    inst.write_file(off, off_text, 0o755)
    inst.write_file(on, on_text, 0o755)
    return off, on


def build_worktable(inst: Installer, desktop: pathlib.Path, title: str, openclaw_root: pathlib.Path,
                    workspace: pathlib.Path, skills: pathlib.Path, projects: pathlib.Path,
                    package_heartbeat_names: tuple[str, str]) -> pathlib.Path:
    root = desktop / title
    if root.exists():
        inst.rmtree(root)
    inst.mkdir(root)
    inst.mkdir(root / "其他快捷方式")
    inst.symlink_force(openclaw_root, root / "01-OpenClaw母文件夹")
    inst.symlink_force(workspace, root / "02-Workspace")
    inst.symlink_force(skills, root / "03-Skills")
    inst.symlink_force(projects, root / "04-Projects")
    small = textwrap.dedent(f'''\
        OpenClaw 工作台（小白版）

        你最常用的入口都在这里：
        1. 01-OpenClaw母文件夹：OpenClaw 总目录
        2. 02-Workspace：日常主要工作区
        3. 03-Skills：skills 主目录
        4. 04-Projects：项目目录
        5. 其他快捷方式：你自己后续可继续补充常用分组

        Heartbeat 开关：
        - {package_heartbeat_names[0]}
        - {package_heartbeat_names[1]}

        说明：
        - 关闭时会同时改持久配置 + 关闭运行态 heartbeat
        - 恢复时会同时改持久配置 + 打开运行态 heartbeat
        - 验收以 status --deep 为准，不以“感觉像关了”为准
    ''')
    pro = textwrap.dedent('''\
        设计原则
        - 顶层只保留高频入口
        - skills 入口默认指向 workspace/skills
        - Heartbeat 开关采用双写：配置 cadence + runtime toggle
        - macOS 权限不做伪自动化，采用宿主稳定化 + 引导 + 验证
    ''')
    inst.write_file(root / "说明-小白版.txt", small)
    inst.write_file(root / "说明-专业版.txt", pro)
    return root


def maybe_make_app(inst: Installer, desktop: pathlib.Path, host_command: pathlib.Path, title: str) -> pathlib.Path | None:
    osa = shutil.which("osacompile")
    if not osa:
        return None
    app_path = desktop / f"{title}.app"
    source = textwrap.dedent(f'''\
        tell application "Terminal"
            activate
            do script quoted form of POSIX path of {json.dumps(str(host_command))}
        end tell
    ''')
    inst.record("build_app", path=str(app_path), title=title)
    if inst.dry_run:
        return app_path
    temp = desktop / f".{title}.applescript"
    temp.write_text(source, encoding="utf-8")
    try:
        run([osa, "-o", str(app_path), str(temp)])
    finally:
        temp.unlink(missing_ok=True)
    return app_path


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Install OpenClaw macOS host kit assets for the current user.")
    ap.add_argument("--home", default=str(pathlib.Path.home()))
    ap.add_argument("--workspace", default="")
    ap.add_argument("--desktop-title", default="OpenClaw 工作台")
    ap.add_argument("--heartbeat-cadence", default="30m")
    ap.add_argument("--openclaw-bin", default="/opt/homebrew/bin/openclaw")
    ap.add_argument("--gateway-port", type=int, default=28789)
    ap.add_argument("--generate-app", action="store_true")
    ap.add_argument("--host-env-file", default="")
    ap.add_argument("--package-only-heartbeat", action="store_true", help="Only keep heartbeat command copies inside the worktable package.")
    ap.add_argument("--mode", choices=["full", "host-only", "desktop-only", "heartbeat-only"], default="full")
    ap.add_argument("--replace-existing-worktable", default="", help="Archive this existing Desktop folder before creating the new worktable; never deletes it directly.")
    ap.add_argument("--archive-root-name", default="OpenClaw旧入口归档")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true", help="Output machine-readable JSON summary only.")
    return ap.parse_args()


def main() -> None:
    args = parse_args()
    inst = Installer(dry_run=args.dry_run)

    home = pathlib.Path(args.home).expanduser()
    openclaw_root = home / ".openclaw"
    workspace = pathlib.Path(args.workspace).expanduser() if args.workspace else (openclaw_root / "workspace")
    desktop = home / "Desktop"
    skills = workspace / "skills"
    projects = workspace / "projects"
    config_path = openclaw_root / "openclaw.json"
    host_env = pathlib.Path(args.host_env_file).expanduser() if args.host_env_file else (home / ".openclaw-host" / "openclaw-host.env")

    summary: dict[str, Any] = {
        "mode": args.mode,
        "dry_run": args.dry_run,
        "home": str(home),
        "workspace": str(workspace),
        "desktop": str(desktop),
        "worktable": None,
        "host_script": None,
        "host_stop_script": None,
        "host_env": None,
        "host_command": None,
        "restore_command": None,
        "permissions_command": None,
        "heartbeat_off": None,
        "heartbeat_on": None,
        "archived_worktable": None,
        "actions": inst.actions,
    }

    if args.replace_existing_worktable:
        archived = archive_existing_worktable(inst, desktop, args.replace_existing_worktable, args.archive_root_name)
        summary["archived_worktable"] = str(archived) if archived else None

    if args.mode in {"full", "host-only"}:
        build_host_env(inst, host_env, home, args.gateway_port)
        host_sh, stop_sh = build_host_scripts(inst, home, host_env, args.gateway_port)
        host_cmd = build_host_command(inst, desktop, host_sh)
        restore_cmd = build_restore_command(inst, desktop, stop_sh)
        summary["host_script"] = str(host_sh)
        summary["host_stop_script"] = str(stop_sh)
        summary["host_env"] = str(host_env)
        summary["host_command"] = str(host_cmd)
        summary["restore_command"] = str(restore_cmd)
        if args.generate_app:
            app = maybe_make_app(inst, desktop, host_cmd, "OpenClaw Host")
            summary["app"] = str(app) if app else None

    if args.mode in {"full", "desktop-only"}:
        perms = build_permissions_command(inst, desktop)
        worktable = build_worktable(
            inst=inst,
            desktop=desktop,
            title=args.desktop_title,
            openclaw_root=openclaw_root,
            workspace=workspace,
            skills=skills,
            projects=projects,
            package_heartbeat_names=("05-专注模式（关闭自动心跳）.command", "06-恢复自动心跳.command"),
        )
        summary["permissions_command"] = str(perms)
        summary["worktable"] = str(worktable)

    if args.mode in {"full", "heartbeat-only"}:
        off, on = build_heartbeat_commands(inst, desktop, config_path, args.heartbeat_cadence, args.openclaw_bin)
        summary["heartbeat_off"] = str(off)
        summary["heartbeat_on"] = str(on)
        existing_worktable = pathlib.Path(summary["worktable"]) if summary["worktable"] else (desktop / args.desktop_title)
        should_mirror_into_worktable = summary["worktable"] is not None or existing_worktable.exists() or args.mode == "full"
        if should_mirror_into_worktable:
            pkg_off = existing_worktable / "05-专注模式（关闭自动心跳）.command"
            pkg_on = existing_worktable / "06-恢复自动心跳.command"
            inst.copy2(off, pkg_off)
            inst.copy2(on, pkg_on)
            if args.package_only_heartbeat:
                inst.unlink(off)
                inst.unlink(on)
                summary["heartbeat_off"] = str(pkg_off)
                summary["heartbeat_on"] = str(pkg_on)

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
