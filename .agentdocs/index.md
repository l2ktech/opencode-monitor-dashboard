# OpenCode Monitor 文档索引

## 项目概述
OpenCode Monitor 是一个多设备会话监控系统，可以将所有设备的 OpenCode 会话聚合到中央 Dashboard，在单一页面统一查看。

## 使用文档

### 设备配置
- `device-setup-guide.md` - 添加新设备的完整指南，包含 Mac、Windows、Android 设备的配置步骤

## 全局重要记忆

### 技术架构
- **中央 Dashboard**：运行在 Mac Mini (192.168.1.4:38002)，聚合所有设备数据
- **Agent 服务**：每个设备运行独立的 HTTP Agent 服务，提供本地会话数据 API
- **通信方式**：HTTP API（不支持 SSH），Dashboard 通过 HTTP 请求获取设备数据
- **数据刷新**：Dashboard 每 5-10 秒自动刷新所有设备数据

### 配置文件
- `dashboard-config.json`：设备配置文件，包含所有 Agent 设备的连接信息
- 配置格式：`{id, name, url, enabled}`
- `url` 格式：`http://<设备IP>:38002` 或 `local`（本地设备）

### 添加设备流程
1. 在目标设备上克隆项目并安装依赖（Python 3 + flask + requests）
2. 启动 Agent 服务：`python3 app.py`
3. 确认设备在同一局域网，获取设备 IP
4. 在 Mac Mini 的 `dashboard-config.json` 中添加设备配置
5. 重启 Mac Mini 的 Dashboard 服务

### 设备支持状态
- ✅ Mac：完全支持
- ✅ Windows：完全支持
- ⚠️ Android：需要特殊处理（Termux 环境），暂不推荐
- ❌ Linux：未测试（理论上支持）

### 网络要求
- 所有设备必须在同一局域网
- 设备之间能够互相 ping 通
- 端口 38002 必须开放（防火墙设置）

### 测试方法
```bash
# 测试设备 Agent 是否正常运行
curl http://<设备IP>:38002/api/sessions
```