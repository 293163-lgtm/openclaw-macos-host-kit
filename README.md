# openclaw-macos-host-kit

**A field-tested OpenClaw skill for turning a macOS machine into a stable desktop OpenClaw workstation.**

**English** | [中文](./README.zh-CN.md)

![openclaw-macos-host-kit banner](./assets/openclaw-macos-host-kit-banner.svg)

`openclaw-macos-host-kit` packages the hard-earned operational pattern for running OpenClaw on real Macs: stable host entrypoints, clean desktop launchers, practical permission guidance, and heartbeat controls that actually work.

It was built from real multi-machine rollout work and validated on more than one macOS host.

## Why it exists

OpenClaw on macOS can fail in boring but costly ways:

- LaunchAgent environments may not refresh the way you expect.
- macOS privacy permissions cannot be honestly “auto-granted” by a script.
- Desktop shortcuts tend to become a pile of half-working commands.
- “Disable heartbeat” can look successful while the main cadence still appears active.

This skill turns those lessons into a reusable kit.

## Core capabilities

- Create a stable Terminal-hosted OpenClaw gateway launcher.
- Generate `OpenClaw Host.command` and optional `OpenClaw Host.app`.
- Generate a clean desktop workbench for OpenClaw folders.
- Generate permission guidance entrypoints for macOS privacy settings.
- Generate real heartbeat on/off commands using config + runtime toggles.
- Support installation modes: full, host-only, desktop-only, heartbeat-only.
- Support dry-run and JSON output for safer remote operations.
- Safely archive an old desktop workbench before replacing it.

## What makes it different

This is not a cosmetic shortcut generator.

The heartbeat buttons use the verified two-layer control path:

- disable: set `agents.defaults.heartbeat.every = ""`, `target = "none"`, then run `openclaw system heartbeat disable`
- enable: set `every = "30m"` or a custom cadence, keep `target = "none"`, then run `openclaw system heartbeat enable`

The success criterion is explicit:

- disabled state: `openclaw status --deep` shows `disabled (main)`
- restored state: `openclaw status --deep` shows `30m (main)` or your configured cadence

## Scope and boundaries

This skill **does not** pretend to silently grant macOS TCC permissions.

It does provide:

- stable host anchoring patterns
- settings shortcuts
- desktop artifacts
- verification scripts
- practical operator guidance

## Installation

Download the `.skill` package from the latest GitHub Release, then install it into your OpenClaw skills directory.

The packaged artifact is available under:

```text
dist/openclaw-macos-host-kit.skill
```

## Basic usage

From a machine that already has the skill source available:

```bash
python3 skill/openclaw-macos-host-kit/scripts/install_host_kit.py --mode full --generate-app --json
```

Dry run first:

```bash
python3 skill/openclaw-macos-host-kit/scripts/install_host_kit.py --dry-run --json
```

Only rebuild heartbeat controls:

```bash
python3 skill/openclaw-macos-host-kit/scripts/install_host_kit.py --mode heartbeat-only
```

Safely replace an old desktop workbench:

```bash
python3 skill/openclaw-macos-host-kit/scripts/install_host_kit.py \
  --replace-existing-worktable "OpenClaw Desk" \
  --mode full \
  --generate-app
```

Old workbenches are archived, not deleted.

## Example prompts

- “Set up this Mac as a stable OpenClaw workstation.”
- “Generate a clean OpenClaw desktop workbench.”
- “Create heartbeat on/off buttons that actually work.”
- “Migrate my old OpenClaw desktop shortcuts into a safer new layout.”
- “Dry-run the OpenClaw macOS host kit before touching this machine.”

## Validation posture

This initial public release is marked `v0.1.0` because it is intentionally conservative: useful, tested, and bounded, but still expected to evolve as more real macOS hosts are validated.

## Repository layout

```text
skill/openclaw-macos-host-kit/   # skill source
dist/                            # packaged .skill artifact
releases/                        # release notes
assets/                          # banner / visual assets
```

## License

MIT
