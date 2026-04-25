# 安装与使用（中文）

## 一句话用途
把一台 macOS 机器整理成稳定的 OpenClaw 工作机，并生成：
- Host 启动入口
- Host 恢复后台服务入口
- 桌面工作台
- 权限引导入口
- 真正有效的 Heartbeat 开关

## 快速开始
先预检：

```bash
command -v openclaw
openclaw status --deep
command -v osacompile
ls -la ~/Desktop
```

再执行：

```bash
python3 skills/openclaw-macos-host-kit/scripts/install_host_kit.py --generate-app --json
```

若要替换旧工作台，使用安全归档模式，不直接删除：

```bash
python3 skills/openclaw-macos-host-kit/scripts/install_host_kit.py \
  --generate-app \
  --replace-existing-worktable "OpenClaw Desk"
```

默认会生成：
- `OpenClaw Host.command`
- `恢复OpenClaw后台服务.command`
- `OpenClaw Host.app`（若本机支持）
- `OpenClaw权限收口.command`
- `OpenClaw-专注模式（关闭自动心跳）.command`
- `OpenClaw-恢复自动心跳.command`
- `OpenClaw 工作台/`

## 安装模式

### 完整安装
```bash
python3 skills/openclaw-macos-host-kit/scripts/install_host_kit.py --mode full --generate-app
```

### 只生成宿主入口
```bash
python3 skills/openclaw-macos-host-kit/scripts/install_host_kit.py --mode host-only --generate-app
```

### 只生成桌面工作台与权限入口
```bash
python3 skills/openclaw-macos-host-kit/scripts/install_host_kit.py --mode desktop-only
```

### 只生成 Heartbeat 开关
```bash
python3 skills/openclaw-macos-host-kit/scripts/install_host_kit.py --mode heartbeat-only
```

说明：
- 若现有 `OpenClaw 工作台` 已存在，会同步把开关镜像进去
- 若工作台不存在，则只生成桌面根目录按钮，不会偷偷造一个半残目录

### 安全归档旧工作台
```bash
python3 skills/openclaw-macos-host-kit/scripts/install_host_kit.py --replace-existing-worktable "OpenClaw Desk"
```

说明：
- 旧目录不会被直接删除
- 会移动到桌面的 `OpenClaw旧入口归档/`
- 适合从旧入口正式切换到新工作台

## Dry run
```bash
python3 skills/openclaw-macos-host-kit/scripts/install_host_kit.py --dry-run --json
```

## 常用参数

### 自定义 heartbeat 节奏
```bash
python3 skills/openclaw-macos-host-kit/scripts/install_host_kit.py --heartbeat-cadence 2h
```

### 指定 workspace
```bash
python3 skills/openclaw-macos-host-kit/scripts/install_host_kit.py --workspace ~/my-openclaw-workspace
```

### 只保留工作台里的 heartbeat 按钮
```bash
python3 skills/openclaw-macos-host-kit/scripts/install_host_kit.py --package-only-heartbeat
```

## 安装后应该看到什么
桌面上通常会出现：
- `OpenClaw Host.command`
- `恢复OpenClaw后台服务.command`
- `OpenClaw Host.app`（若开启 `--generate-app` 且本机有 `osacompile`）
- `OpenClaw权限收口.command`
- `OpenClaw-专注模式（关闭自动心跳）.command`
- `OpenClaw-恢复自动心跳.command`
- `OpenClaw 工作台/`

`OpenClaw 工作台/` 内应包含：
- `01-OpenClaw母文件夹`
- `02-Workspace`
- `03-Skills`
- `04-Projects`
- `05-专注模式（关闭自动心跳）.command`
- `06-恢复自动心跳.command`
- 说明文件

## Heartbeat 验收标准
### 关闭成功
```bash
openclaw status --deep
```
看到：
```text
disabled (main)
```

### 恢复成功
```bash
openclaw status --deep
```
看到：
```text
30m (main)
```
或你自定义的 cadence。

## 边界说明
- 这个 skill **不能静默自动授予** macOS 隐私权限
- 它做的是：稳定宿主 + 打开正确设置页 + 提供验证路径
- 如果你的机器本来 LaunchAgent 已经非常稳定，也可以只用它生成桌面包和 heartbeat 开关
