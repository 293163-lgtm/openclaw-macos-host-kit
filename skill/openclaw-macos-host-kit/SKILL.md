---
name: openclaw-macos-host-kit
description: 在 macOS 上为 OpenClaw 创建稳定的桌面宿主方案、桌面启动 App、桌面快捷方式包、权限引导，以及真正有效的 Heartbeat 开关。适用于把一台新 Mac 配成可长期使用的 OpenClaw 工作机，尤其是用户说“帮我把这台 Mac 配成能稳定跑 OpenClaw”“做桌面启动入口”“整理快捷方式”“做真正有效的 heartbeat 开关”“把这套方案做成可复用模板/skill”时。
---

# openclaw-macos-host-kit

把一台 macOS 机器整理成可长期使用的 OpenClaw 工作机：
- 稳定宿主
- 清晰桌面入口
- 权限引导
- 真正有效的 heartbeat 开关
- 可复用到别的 Mac

## 何时使用

当用户要做以下任一类事时，使用本 skill：
- 在 macOS 上部署/收口 OpenClaw 桌面宿主方案
- 创建 OpenClaw Host.app / .command 启动入口
- 生成桌面快捷方式包（workspace / skills / projects 等）
- 创建或修复 heartbeat 开关，并要求“真的有效”
- 把已验证过的一台 Mac 的 OpenClaw 桌面化方案抽象成可复用模板

## 先读什么

1. 先读 `references/cn.md` —— 中文入口与交付口径
2. 再读 `references/architecture.md` —— 了解宿主模式、权限边界、heartbeat 原理
3. 执行前读 `references/preflight.md` —— 做机器预检
4. 需要落地时，优先使用 `scripts/install_host_kit.py`

## 核心立场

- **不要假装 macOS 权限可以被静默自动授予。**
  TCC（辅助功能、屏幕录制、全磁盘访问）只能通过稳定宿主 + 权限引导 + 验证来完成。
- **优先稳定，而不是“看起来自动化”。**
  若 LaunchAgent 路线对权限或环境变量不稳定，优先使用 Terminal-hosted 模式。
- **Heartbeat 开关必须基于真实运行机制。**
  不能只改 `heartbeat.target`，也不能只切运行态开关。
- **桌面入口要像产品，不像垃圾堆。**
  顶层只保留高频入口，其他收进整理分组。

## 标准工作流

### Phase 1 — Preflight
先确认：
- `openclaw` CLI 可用
- 目标机器是 macOS
- 目标用户 home / workspace / Desktop 路径清楚
- 当前 OpenClaw 是 LaunchAgent 模式还是 Terminal-hosted 模式
- 是否已有旧桌面入口需要兼容或清理

使用：`references/preflight.md`

### Phase 2 — Host Strategy
判断宿主策略：
- 若 LaunchAgent 在该机上权限与 env 都稳定，可保留
- 若 LaunchAgent 对权限/TCC/env 不稳定，切到 Terminal-hosted 模式

复用脚本模板时：
- 生成 `openclaw-host.sh`
- 生成 `openclaw-host-stop.sh`
- 生成宿主 env 文件
- 生成 `OpenClaw Host.command`
- 如需要，再生成 `OpenClaw Host.app`

### Phase 3 — Desktop Package
默认生成工作台目录，包含：
- `01-OpenClaw母文件夹`
- `02-Workspace`
- `03-Skills`
- `04-Projects`
- `其他快捷方式`
- `说明-小白版.txt`
- `说明-专业版.txt`

是否保留桌面根目录重复入口，按用户偏好决定。

### Phase 4 — Heartbeat Controls
**关闭 heartbeat 的有效条件：**
- 配置写入：
  - `agents.defaults.heartbeat.every = ""`
  - `agents.defaults.heartbeat.target = "none"`
- 再执行：
  - `openclaw system heartbeat disable`

**恢复 heartbeat 的有效条件：**
- 配置写入：
  - `agents.defaults.heartbeat.every = "30m"`（或用户指定 cadence）
  - `agents.defaults.heartbeat.target = "none"`
- 再执行：
  - `openclaw system heartbeat enable`

**验收标准：**
- 关闭后 `openclaw status --deep` 显示 `disabled (main)`
- 恢复后显示 `30m (main)` 或用户指定节奏

### Phase 5 — Permissions Guidance
不要承诺自动授予权限。
应提供：
- 权限引导入口（系统设置 URL）
- 稳定宿主建议
- 最小验证步骤

### Phase 6 — Verification
最小验证至少包括：
- `openclaw status --deep`
- 桌面文件存在性检查
- heartbeat 开/关各一次
- 若该机涉及 TCC 工作流，再做对应能力验证

## 脚本优先级

- 优先调用 `scripts/install_host_kit.py`
- 若只需要重建桌面包或 heartbeat 开关，可用脚本参数做局部执行
- 不要把复杂 shell 直接散落在对话里；把可复用逻辑收进脚本

## 适配边界

这个 skill 应该参数化而不是硬编码：
- 用户名 / home
- workspace 路径
- Desktop 路径
- 桌面包标题
- heartbeat cadence
- 是否生成 .app
- 是否保留桌面根目录快捷入口
- 是否安全归档旧工作台（归档，不直接删除）

## 必须避免

- 只改 `heartbeat.target` 就宣称 heartbeat 关闭成功
- 把某台机器的 secret env 原样写死进通用脚本
- 假装能自动拿到系统隐私权限
- 桌面入口越做越乱
- 没验证就删旧入口；旧入口只能先归档，不能直接删除
