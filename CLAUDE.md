# OpenCode Monitor Dashboard - 开发规范

## 运行方式

```bash
cd dashboard-ocmonitor
python app.py
```

应用默认运行在 `http://0.0.0.0:38002`

## 依赖

- Python 3.8+
- Flask: `pip install flask`
- requests: `pip install requests`

## 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `OCMONITOR_DATA_DIR` | `~/.local/share/opencode/storage/message` | 本地会话数据目录 |
| `OCMONITOR_PORT` | `38002` | 应用监听端口 |
| `OCMONITOR_API_TOKEN` | 未设置 | API 认证 token（可选） |

## 测试

```bash
cd dashboard-ocmonitor
pytest tests/
```

## Lint

暂无配置。

## API 端点

- `GET /` - 仪表板 UI
- `GET /health` - 健康检查
- `GET /api/devices` - 设备列表（需认证）
- `GET /api/sessions` - 会话数据（需认证）

### 查询参数（/api/sessions）

- `sort=device|active` - 排序字段
- `order=asc|desc` - 排序方向
- `filter=<name>` - 按设备名过滤

### 认证

如果设置了 `OCMONITOR_API_TOKEN`，API 请求需携带：
```
Authorization: Bearer <token>
```

前端会从 `localStorage.getItem('ocmonitor_token')` 读取 token。