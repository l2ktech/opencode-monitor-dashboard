#!/bin/bash
# MacBook Agent 部署脚本
# 请在 MacBook 本地终端运行此脚本

echo "================================================"
echo "   MacBook Agent 部署脚本"
echo "================================================"
echo ""

MACBOOK_IP="192.168.1.246"
MACMINI_IP="192.168.1.4"

echo "📋 配置信息："
echo "  MacBook IP: $MACBOOK_IP"
echo "  Mac Mini Dashboard: http://$MACMINI_IP:38002"
echo ""

cd ~/

if [ -d "opencode-monitor-dashboard" ]; then
    echo "⚠️  目录已存在，是否删除重新部署？(y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        rm -rf opencode-monitor-dashboard
    else
        cd opencode-monitor-dashboard
    fi
fi

if [ ! -d "opencode-monitor-dashboard" ]; then
    echo "📥 克隆项目..."
    git clone https://github.com/l2ktech/opencode-monitor-dashboard.git
    cd opencode-monitor-dashboard
fi

echo ""
echo "📦 安装依赖..."
pip3 install -r requirements.txt

echo ""
echo "🚀 启动 Agent 服务..."
pkill -f "python3 app.py" 2>/dev/null || true
nohup python3 app.py > logs/app.log 2>&1 &

sleep 3

if lsof -i :38002 > /dev/null 2>&1; then
    echo "✅ MacBook Agent 启动成功！"
    echo ""
    echo "访问地址: http://$MACBOOK_IP:38002"
    echo ""
    echo "下一步："
    echo "1. 在 Mac Mini 上更新配置文件"
    echo "2. SSH 到 Mac Mini 执行："
    echo "   ssh wzy@$MACMINI_IP"
    echo "   cd /Users/wzy/01-note/dashboard-ocmonitor"
    echo "   nano dashboard-config.json"
    echo ""
    echo "添加以下配置："
    echo '{'
    echo '  "devices": ['
    echo '    {'
    echo '      "id": "local",'
    echo '      "name": "Mac Mini",'
    echo '      "url": "local",'
    echo '      "enabled": true'
    echo '    },'
    echo '    {'
    echo '      "id": "macbook-01",'
    echo '      "name": "MacBook",'
    echo '      "url": "http://'"$MACBOOK_IP"':38002",'
    echo '      "enabled": true'
    echo '    }'
    echo '  ]'
    echo '}'
    echo ""
    echo "然后重启 Mac Mini Dashboard："
    echo "   ./quick-start.sh"
else
    echo "❌ MacBook Agent 启动失败"
    echo "查看日志: tail -f ~/opencode-monitor-dashboard/logs/app.log"
fi
