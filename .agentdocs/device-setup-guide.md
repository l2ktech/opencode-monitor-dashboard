# 设备添加指南

本文档说明如何将新设备添加到 OpenCode Monitor 系统。

## 快速概览

每个设备需要：
1. 安装 Python 3 环境
2. 克隆项目并安装依赖
3. 启动 Agent 服务（端口 38002）
4. 在 Mac Mini 的配置文件中注册设备

## Mac 设备配置

### 前提条件
- macOS 10.15 或更高版本
- Python 3.7 或更高版本
- 网络连接到同一局域网

### 配置步骤

```bash
# 1. 克隆项目
git clone https://github.com/your-repo/dashboard-ocmonitor.git
cd dashboard-ocmonitor

# 2. 安装依赖
pip3 install flask requests

# 3. 启动 Agent
python3 app.py
```

### 获取设备 IP
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```
或
```bash
ipconfig getifaddr en0
```

## Windows 设备配置

### 前提条件
- Windows 10 或更高版本
- Python 3.7 或更高版本（从 [python.org](https://www.python.org/downloads/) 安装）
- Git（从 [git-scm.com](https://git-scm.com/download/win) 安装）

### 配置步骤

```powershell
# 1. 克隆项目
git clone https://github.com/your-repo/dashboard-ocmonitor.git
cd dashboard-ocmonitor

# 2. 安装依赖
pip install flask requests

# 3. 启动 Agent
python app.py
```

### 获取设备 IP
```powershell
ipconfig | findstr "IPv4"
```

## Android 设备配置

### 注意事项
⚠️ Android 设备需要特殊处理，暂不推荐使用。

### 原因
- Android 的 OpenCode 数据存储路径与桌面系统不同
- 需要安装 Termux 或类似终端模拟器
- 需要配置 Python 环境
- 网络配置更复杂

### 如果必须使用 Android
1. 安装 Termux 应用
2. 在 Termux 中安装 Python
3. 克隆项目并安装依赖
4. 修改代码以适配 Android 文件路径

## 在 Mac Mini 注册设备

### 编辑配置文件

打开 `dashboard-ocmonitor/dashboard-config.json`：

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
      "url": "http://192.168.1.246:38002",
      "enabled": true
    },
    {
      "id": "windows-01",
      "name": "Windows PC",
      "url": "http://192.168.1.XXX:38002",
      "enabled": true
    }
  ]
}
```

### 配置说明

| 字段 | 说明 | 示例 |
|------|------|------|
| `id` | 设备唯一标识（英文、数字、短横线） | `windows-01` |
| `name` | 设备显示名称（中文） | `Windows PC` |
| `url` | 设备 Agent 服务地址 | `http://192.168.1.XXX:38002` |
| `enabled` | 是否启用 | `true` |

**重要**：`url` 必须是 `http://<设备IP>:38002`，不要省略端口号。

### 重启服务

配置完成后，重启 Mac Mini 的 Dashboard：

```bash
# 停止当前服务（Ctrl+C）
# 重新启动
cd dashboard-ocmonitor
python3 app.py
```

## 测试连接

### 测试设备 Agent 是否正常运行

在 Mac Mini 上执行：

```bash
curl http://<设备IP>:38002/api/sessions
```

**预期结果**：返回 JSON 格式的会话数据数组。

### 测试 Dashboard 是否能看到设备

1. 打开浏览器访问：`http://192.168.1.4:38002`
2. 查看页面上的会话卡片
3. 确认显示了新设备的会话
4. 检查会话卡片上的设备标签

## 网络要求

### 必须满足的条件

- ✅ 所有设备在同一局域网
- ✅ 设备之间能够互相 ping 通
- ✅ 端口 38002 未被占用
- ✅ 防火墙允许端口 38002 的入站连接

### 检查网络连接

```bash
# 在 Mac Mini 上测试是否能 ping 通其他设备
ping <设备IP>

# 测试端口是否开放
nc -zv <设备IP> 38002
```

## 常见问题

### 1. Dashboard 看不到新设备

**可能原因**：
- 设备未启动 Agent 服务
- 防火墙阻止了连接
- 配置文件中的 IP 地址错误

**解决方法**：
```bash
# 测试设备是否在线
ping <设备IP>

# 测试 Agent 服务是否运行
curl http://<设备IP>:38002/api/sessions

# 检查防火墙设置
```

### 2. 无法连接到设备 Agent

**可能原因**：
- 设备的防火墙阻止了 38002 端口
- Agent 服务未启动
- IP 地址错误

**解决方法**：
- 检查 Agent 是否运行：`ps aux | grep app.py`
- 重新获取设备 IP 地址
- 临时关闭防火墙测试连接

### 3. 设备会话数据不显示

**可能原因**：
- OpenCode 未在该设备上使用过
- OpenCode 数据路径不正确
- 数据格式有问题

**解决方法**：
- 在新设备上启动 OpenCode 并创建会话
- 检查 `~/.local/share/opencode/storage/message` 目录是否存在

### 4. Windows 设备无法启动

**可能原因**：
- Python 未正确安装或未添加到 PATH
- 依赖安装失败

**解决方法**：
```powershell
# 检查 Python 版本
python --version

# 重新安装依赖
pip install flask requests --upgrade
```

## 安全注意事项

### 网络安全
- ⚠️ 当前系统仅在局域网内运行，建议不要暴露到公网
- ⚠️ 没有身份验证机制，任何局域网设备都可以访问
- ⚠️ 建议在网络层面限制访问（如路由器 ACL）

### 数据隐私
- ⚠️ 会话数据包含完整的对话内容，确保局域网环境可信
- ⚠️ 不要在不安全的公共网络环境使用

## 下一步

设备添加成功后：
1. 访问 `http://192.168.1.4:38002` 查看所有设备会话
2. 使用 `scan-devices.sh` 扫描局域网中的设备
3. 根据需要添加更多设备

## 扫描局域网设备

在 Mac Mini 上执行扫描脚本：

```bash
cd dashboard-ocmonitor
./scan-devices.sh
```

该脚本会自动发现：
- 局域网中的在线设备
- 运行 Dashboard 或 Agent 的设备
- 设备的 IP 地址和服务状态