# 多设备监控部署指南

## 架构说明

- **Mac Mini**：中央 Dashboard（聚合所有设备数据）
- **MacBook/其他设备**：Agent（提供本地会话数据）

## 一、在 Mac Mini 上（中央 Dashboard）

### 1.1 当前状态
✅ 已完成：
- Dashboard 服务运行在 `http://192.168.1.4:38002`
- 支持多设备聚合
- 已安装依赖：`requests` 库

### 1.2 配置设备列表

编辑配置文件：
```bash
cd /Users/wzy/01-note/dashboard-ocmonitor
nano dashboard-config.json
```

添加 MacBook 设备：
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
      "name": "MacBook Pro",
      "url": "http://192.168.1.10:38002",
      "enabled": true
    }
  ]
}
```

**重要**：将 `192.168.1.10` 替换为 MacBook 的实际 IP 地址。

### 1.3 重启服务

```bash
cd /Users/wzy/01-note/dashboard-ocmonitor
pkill -f "python3 app.py"
nohup python3 app.py > logs/app.log 2>&1 &
```

或使用 LaunchAgent 重启：
```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.ocmonitor.dashboard.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.ocmonitor.dashboard.plist
```

## 二、在 MacBook 上（Agent）

### 2.1 克隆项目

```bash
# 方法1：从 GitHub 克隆
cd ~/
git clone https://github.com/l2ktech/opencode-monitor-dashboard.git
cd opencode-monitor-dashboard

# 方法2：从 Mac Mini 复制
scp -r wzy@192.168.1.4:/Users/wzy/01-note/dashboard-ocmonitor ~/opencode-monitor-dashboard
cd ~/opencode-monitor-dashboard
```

### 2.2 安装依赖

```bash
pip3 install -r requirements.txt
```

### 2.3 配置设备信息（可选）

编辑 `dashboard-config.json`：
```json
{
  "devices": [
    {
      "id": "local",
      "name": "MacBook Pro",
      "url": "local",
      "enabled": true
    }
  ]
}
```

### 2.4 启动 Agent 服务

```bash
nohup python3 app.py > logs/app.log 2>&1 &
```

### 2.5 验证服务

```bash
curl http://localhost:38002/api/sessions
```

应该能看到 JSON 数据返回。

### 2.6 配置自动启动（可选）

```bash
./scripts/install-service.sh
```

## 三、查看 MacBook 的 IP 地址

在 MacBook 上执行：
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

或者：
```bash
ipconfig getifaddr en0
```

## 四、测试多设备聚合

### 4.1 在 Mac Mini 上测试 API

```bash
# 测试本地数据
curl http://localhost:38002/api/sessions

# 测试设备列表
curl http://localhost:38002/api/devices

# 测试从 MacBook 拉取数据（需先在配置中添加 MacBook）
# 重启服务后会自动聚合
```

### 4.2 访问 Dashboard

在浏览器（iPad/电脑）访问：
- **Mac Mini Dashboard**：http://192.168.1.4:38002
- **MacBook Agent**：http://192.168.1.10:38002（仅查看本地）

### 4.3 查看会话卡片

成功配置后，Mac Mini 的 Dashboard 会显示：
- 本地会话：标签显示 "Mac Mini"
- MacBook 会话：标签显示 "MacBook Pro"

## 五、故障排查

### 5.1 MacBook Agent 无法访问

检查防火墙：
```bash
# 在 MacBook 上
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
```

临时关闭防火墙测试：
```bash
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off
```

### 5.2 Mac Mini 无法拉取 MacBook 数据

检查网络连通性：
```bash
# 在 Mac Mini 上
ping 192.168.1.10
curl http://192.168.1.10:38002/api/sessions
```

检查 MacBook Agent 是否运行：
```bash
# 在 MacBook 上
lsof -i :38002
```

### 5.3 查看日志

```bash
# Mac Mini
tail -f /Users/wzy/01-note/dashboard-ocmonitor/logs/app.log

# MacBook
tail -f ~/opencode-monitor-dashboard/logs/app.log
```

## 六、添加更多设备

重复"二、在 MacBook 上（Agent）"的步骤，然后在 Mac Mini 的 `dashboard-config.json` 中添加设备：

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
      "name": "MacBook Pro",
      "url": "http://192.168.1.10:38002",
      "enabled": true
    },
    {
      "id": "imac-01",
      "name": "iMac",
      "url": "http://192.168.1.20:38002",
      "enabled": true
    }
  ]
}
```

每次修改配置后，重启 Mac Mini 的 Dashboard 服务。

## 七、当前功能

✅ **已实现**：
- 多设备数据聚合
- 会话卡片显示设备标签
- 子代理/模型统计（全局聚合）
- 自动刷新（10秒）

🔄 **后续增强**：
- 设备在线/离线状态指示
- 设备筛选器
- 按设备统计（成本、Tokens）
- WebSocket 实时推送

## 八、快速命令参考

```bash
# Mac Mini - 重启 Dashboard
cd /Users/wzy/01-note/dashboard-ocmonitor && pkill -f "python3 app.py" && nohup python3 app.py > logs/app.log 2>&1 &

# MacBook - 启动 Agent
cd ~/opencode-monitor-dashboard && nohup python3 app.py > logs/app.log 2>&1 &

# 查看服务状态
lsof -i :38002

# 查看日志
tail -f logs/app.log

# 测试 API
curl http://localhost:38002/api/sessions | python3 -m json.tool
```
