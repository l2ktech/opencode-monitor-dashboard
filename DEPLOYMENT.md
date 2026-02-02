# 修复与同步脚本使用说明

## 修复单个设备

### 方法 1: 使用修复脚本（推荐）

在 MacBook 上执行：

```bash
cd ~/projects/05-opencode-monitor/dashboard-ocmonitor
bash fix-app.py
```

脚本会自动：
1. 备份原文件
2. 修复 `app.py` 中的 `current_turn_context` 计算逻辑
3. 验证语法

### 方法 2: 手动修复

编辑 `app.py`，找到第 252-269 行，将代码替换为：

```python
recent_tokens = {
    'input': 0,
    'output': 0,
    'cache_write': 0,
    'cache_read': 0
}

for m in reversed(messages):
    if m.get('tokens') is not None and isinstance(m['tokens'], dict):
        msg_input = m['tokens'].get('input', 0) or 0
        msg_cache_read = m['tokens'].get('cache', {}).get('read', 0) or 0
        if msg_input > 0 or msg_cache_read > 0:
            recent_tokens['input'] = msg_input
            recent_tokens['output'] = m['tokens'].get('output', 0) or 0
            recent_tokens['cache_write'] = m['tokens'].get('cache', {}).get('write', 0) or 0
            recent_tokens['cache_read'] = msg_cache_read
            break
```

### 重启服务

修复后重启服务：

```bash
pkill -f 'python.*app.py'
nohup python3 app.py &
```

## 从仓库同步

如果代码在 git 仓库中，可以直接拉取最新代码：

```bash
cd ~/projects/05-opencode-monitor/dashboard-ocmonitor
git pull
```

如果配置了同步脚本，也可以使用：

```bash
bash sync-from-repo.sh
```

## 验证修复

访问 http://192.168.1.246:38002，检查：
1. 活跃会话的"当前"上下文不再显示为 0
2. 显示真实的当前上下文值（如 60.1K、150.2K 等）

## 远程执行（需要 SSH）

如果需要从 Mac Mini 远程执行修复：

```bash
# 方法 1: 复制脚本并执行
scp fix-app.py wzy@192.168.1.246:~/projects/05-opencode-monitor/dashboard-ocmonitor/
ssh wzy@192.168.1.246 "cd ~/projects/05-opencode-monitor/dashboard-ocmonitor && bash fix-app.py && pkill -f 'python.*app.py' && nohup python3 app.py &"

# 方法 2: 使用 git pull
ssh wzy@192.168.1.246 "cd ~/projects/05-opencode-monitor/dashboard-ocmonitor && git pull && pkill -f 'python.*app.py' && nohup python3 app.py &"
```