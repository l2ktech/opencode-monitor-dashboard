#!/bin/bash

set -e

echo "=== Dashboard OC Monitor 诊断工具 ==="
echo ""

PROJECT_DIR="${1:-~/projects/05-opencode-monitor/dashboard-ocmonitor}"

if [ ! -d "$PROJECT_DIR" ]; then
    echo "错误: 目录不存在 $PROJECT_DIR"
    exit 1
fi

cd "$PROJECT_DIR"

echo "1. 检查目录和文件..."
echo "   当前目录: $(pwd)"
echo "   app.py 存在: $([ -f app.py ] && echo '✓' || echo '✗')"
echo "   nohup.out 存在: $([ -f nohup.out ] && echo '✓' || echo '✗')"
echo ""

echo "2. 检查 Python 语法..."
if python3 -m py_compile app.py 2>&1; then
    echo "   ✓ Python 语法正确"
else
    echo "   ✗ Python 语法错误"
    exit 1
fi
echo ""

echo "3. 检查端口占用..."
PORT=$(lsof -i :38002 -t 2>/dev/null | head -1)
if [ -n "$PORT" ]; then
    echo "   ⚠ 端口 38002 被进程占用: $PORT"
    echo "   进程信息:"
    ps -p "$PORT" -o pid,comm,args | tail -1
else
    echo "   ✓ 端口 38002 可用"
fi
echo ""

if [ -f nohup.out ]; then
    echo "4. 查看 nohup.out 错误日志..."
    echo "--- nohup.out 内容 ---"
    tail -50 nohup.out
    echo "--- end ---"
    echo ""
fi

echo "5. 测试直接运行 app.py（5秒超时）..."
timeout 5 python3 app.py 2>&1 || echo "   (5秒后超时或出错)"
echo ""

echo "6. 检查修复状态..."
if grep -q "msg_input > 0 or msg_cache_read > 0" app.py 2>/dev/null; then
    echo "   ✓ app.py 已应用修复"
else
    echo "   ✗ app.py 未修复，需要运行 fix-app.py"
fi
echo ""

echo "=== 诊断完成 ==="
echo ""
echo "建议操作:"
if [ -n "$PORT" ]; then
    echo "1. 杀掉占用端口的进程: kill $PORT"
fi
if [ ! -f nohup.out ] || grep -q "Error\|error\|Exception" nohup.out 2>/dev/null; then
    echo "2. 查看 nohup.out 了解详细错误"
fi
if ! grep -q "msg_input > 0 or msg_cache_read > 0" app.py 2>/dev/null; then
    echo "3. 运行修复: bash fix-app.py"
fi
echo "4. 重启服务: pkill -f 'python.*app.py' && nohup python3 app.py &"