# OpenCode Monitor Dashboard

轻量级 Web 实时监控面板，专为 OpenCode 会话监控与 iPad/平板展示优化。

## 核心特性

- 4-5 列紧凑网格，12-16 会话同屏
- 5 秒自动刷新
- 上下文占用、token 速率、平均延迟、缓存效率、成本统计
- 超出窗口提示：显示“剩余 / 超出 / 需压缩”
- 崩溃自动重启（macOS LaunchAgent / Linux systemd）
- Docker 一键启动

## 快速开始

### 本地运行

```bash
pip3 install -r requirements.txt
python3 app.py
```

访问：`http://localhost:38002`

### Docker

```bash
docker build -t opencode-monitor-dashboard .
docker run -d \
  -p 38002:38002 \
  -v ~/.local/share/opencode:/data/opencode:ro \
  --name opencode-monitor-dashboard \
  opencode-monitor-dashboard
```

### Docker Compose

```bash
docker compose up -d
```

## iPad 使用

1. Mac 与 iPad 在同一网络
2. 查询 IP：
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```
3. Safari 访问：`http://<IP>:38002`

## 环境变量

支持 `.env` 配置：

```bash
OPENCODE_DATA_DIR=~/.local/share/opencode/storage/message
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=38002
AUTO_REFRESH_INTERVAL=5
```

## macOS 服务

```bash
./scripts/install-service.sh
./scripts/start.sh
./scripts/stop.sh
./scripts/restart.sh
./scripts/status.sh
```

## Linux systemd

```bash
cp scripts/opencode-monitor-dashboard.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now opencode-monitor-dashboard
```

## 与 ocmonitor-share / OpenChamber 的关系

- ocmonitor-share：CLI 分析与报表
- OpenChamber：完整开发 IDE
- 本项目：**实时监控面板（iPad/平板专用）**

## 许可证

MIT License
