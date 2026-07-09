# OpenCode Monitor

## Public Portfolio Summary

This repository is a public support entry for AI development operations. It shows a lightweight Python dashboard for monitoring OpenCode sessions across multiple devices, with agent/dashboard deployment notes, tablet-friendly display usage, and conservative local-network assumptions.

For interviews, use it as evidence of operational tooling around AI coding workflows: multi-device session visibility, simple Flask-style service design, deployment scripts, and documentation for repeatable lab setup. It is not a live private fleet snapshot.

## Evidence Entry Points

- [`app.py`](app.py): main dashboard/agent implementation.
- [`MULTI-DEVICE-SETUP.md`](MULTI-DEVICE-SETUP.md) and [`DEPLOYMENT.md`](DEPLOYMENT.md): setup and deployment notes.
- [`.agentdocs/device-setup-guide.md`](.agentdocs/device-setup-guide.md): device onboarding guide.
- [`docker-compose.yml`](docker-compose.yml), [`Dockerfile`](Dockerfile), and `scripts/`: deployment support.

## Public Boundary

This public README uses placeholder hosts instead of real device inventory. Do not publish private dashboard URLs, live device lists, auth tokens, SSH hostnames, reverse-proxy domains, browser/session history, or production monitoring data in this repository.

多设备 OpenCode 会话监控系统，将所有设备的会话聚合到中央 Dashboard，在单一页面统一查看。

## 快速开始

### 中央 Dashboard（Mac Mini）

```bash
cd dashboard-ocmonitor
python3 app.py
```

访问：`http://<dashboard-host>:38002`

### 添加新设备

📖 **详细配置指南**：查看 [`.agentdocs/device-setup-guide.md`](.agentdocs/device-setup-guide.md)

**快速步骤**：
1. 在目标设备上克隆项目并安装依赖
2. 启动 Agent：`python3 app.py`
3. 在 `dashboard-config.json` 中添加设备配置
4. 重启 Dashboard

## 文档

### 核心文档
- [设备添加指南](.agentdocs/device-setup-guide.md) - Mac、Windows、Android 设备配置步骤
- [文档索引](.agentdocs/index.md) - 架构、配置、技术约束

### 功能特性
- ✅ 多设备数据聚合
- ✅ 单页面统一查看
- ✅ 自动刷新（5-10秒）
- ✅ 设备标签标识
- ✅ 支持任意数量设备

## 项目结构

```
dashboard-ocmonitor/
├── .agentdocs/              # 文档目录
│   ├── index.md            # 文档索引
│   └── device-setup-guide.md # 设备配置指南
├── app.py                  # 主程序
├── dashboard-config.json   # 设备配置文件
├── deploy-macbook-agent.sh # MacBook 部署脚本
└── scan-devices.sh         # 局域网设备扫描
```

## 配置文件

### dashboard-config.json

```json
{
  "devices": [
    {
      "id": "local",
      "name": "Mac Mini",
      "url": "local",
      "enabled": true
    },
    {
      "id": "macbook-01",
      "name": "MacBook",
      "url": "http://<device-ip>:38002",
      "enabled": true
    }
  ]
}
```

## 网络要求

- 所有设备在同一局域网
- 端口 38002 开放
- 设备之间可以互相 ping 通

## 测试连接

```bash
# 测试设备 Agent 是否运行
curl http://<设备IP>:38002/api/sessions
```

## 常见问题

查看 [设备添加指南](.agentdocs/device-setup-guide.md#常见问题) 获取详细排查步骤。

## 安全提示

⚠️ 当前系统仅在局域网内运行，不要暴露到公网
⚠️ 没有身份验证机制，确保局域网环境可信