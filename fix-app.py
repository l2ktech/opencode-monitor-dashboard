#!/bin/bash

set -e

echo "正在修复 app.py 中的 current_turn_context 计算逻辑..."

APP_PATH="${1:-./app.py}"

if [ ! -f "$APP_PATH" ]; then
    echo "错误: 找不到 $APP_PATH"
    exit 1
fi

cp "$APP_PATH" "${APP_PATH}.backup.$(date +%Y%m%d_%H%M%S)"
echo "已备份原文件到 ${APP_PATH}.backup.$(date +%Y%m%d_%H%M%S)"

python3 << 'PYTHON_EOF'
import sys
import re

app_path = sys.argv[1] if len(sys.argv) > 1 else "app.py"

with open(app_path, 'r') as f:
    content = f.read()

old_pattern = r"""# Recent tokens
    recent_tokens = \{
        'input': 0,
        'output': 0,
        'cache_write': 0,
        'cache_read': 0
    \}

    # Find last message with valid tokens
    for m in reversed\(messages\):
        if m\.get\('tokens'\) is not None and isinstance\(m\['tokens'\], dict\):
            recent_tokens\['input'\] = m\['tokens'\]\.get\('input', 0\) or 0
            recent_tokens\['output'\] = m\['tokens'\]\.get\('output', 0\) or 0
            recent_tokens\['cache_write'\] = m\['tokens'\]\.get\('cache', \{\}\)\.get\('write', 0\) or 0
            recent_tokens\['cache_read'\] = m\['tokens'\]\.get\('cache', \{\}\)\.get\('read', 0\) or 0
            break"""

new_code = """recent_tokens = {
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
                break"""

new_content = re.sub(old_pattern, new_code, content, flags=re.MULTILINE | re.DOTALL)

if new_content == content:
    print("警告: 未找到匹配的代码模式，可能已经修复过或代码已更新")
    sys.exit(0)

with open(app_path, 'w') as f:
    f.write(new_content)

print("✓ app.py 修复成功")
PYTHON_EOF

echo ""
echo "验证修复..."
python3 -m py_compile "$APP_PATH" && echo "✓ Python 语法检查通过"

echo ""
echo "修复完成！请重启服务："
echo "  pkill -f 'python.*app.py' && nohup python3 app.py &"