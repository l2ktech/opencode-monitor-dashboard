#!/bin/bash

echo "================================================"
echo "   OpenCode Monitor Dashboard - 快速启动"
echo "================================================"
echo ""

cd "$(dirname "$0")"

if lsof -i :38002 > /dev/null 2>&1; then
    echo "⚠️  端口 38002 已被占用"
    echo ""
    read -p "是否停止现有服务并重启？(y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "正在停止现有服务..."
        pkill -f "python3 app.py" || true
        sleep 2
    else
        echo "取消操作"
        exit 0
    fi
fi

echo "正在启动 Dashboard 服务..."
nohup python3 app.py > logs/app.log 2>&1 &
PID=$!

sleep 3

if lsof -i :38002 > /dev/null 2>&1; then
    echo "✅ Dashboard 启动成功！"
    echo ""
    echo "进程 ID: $PID"
    echo ""
    echo "访问地址："
    echo "  - 本地: http://localhost:38002"
    echo "  - 局域网: http://$(ipconfig getifaddr en0 2>/dev/null || echo "获取IP失败"):38002"
    echo ""
    echo "查看日志："
    echo "  tail -f logs/app.log"
    echo ""
    echo "停止服务："
    echo "  pkill -f \"python3 app.py\""
else
    echo "❌ Dashboard 启动失败"
    echo ""
    echo "查看错误日志："
    echo "  tail -20 logs/app.log"
    exit 1
fi
