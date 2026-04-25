# openclaw-macos-host-kit 中文入口

这个 skill 用来把一台 macOS 机器整理成专业可用的 OpenClaw 工作机。

## 它负责什么
- 生成稳定宿主方案（尤其是 Terminal-hosted 路线）
- 生成桌面启动入口（`.command` / `.app`）
- 生成桌面快捷方式包
- 生成真正有效的 Heartbeat 开关
- 给出权限引导与验证步骤

## 它不负责什么
- 不会假装替你静默授予 macOS 的隐私权限
- 不会把某台机器的 secret 直接硬编码进通用模板

## 推荐阅读顺序
1. `SKILL.md`
2. `architecture.md`
3. `preflight.md`
4. 运行 `scripts/install_host_kit.py --help`

## 交付标准
- 桌面入口清晰
- Heartbeat 开关实测有效
- 宿主模式清楚
- 权限边界说人话
- 另一台 Mac 能按同一 skill 复用
