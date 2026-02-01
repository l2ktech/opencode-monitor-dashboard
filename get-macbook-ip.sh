#!/bin/bash

# 获取 MacBook 的 IP 地址
MACBOOK_IP=$(ipconfig getifaddr en0)

if [ -z "$MACBOOK_IP" ]; then
    echo "❌ 无法获取 MacBook IP 地址"
    echo "请手动检查网络连接"
    exit 1
fi

echo "✅ MacBook IP 地址: $MACBOOK_IP"
echo ""
echo "📋 请在 Mac Mini 的配置文件中使用此 IP："
echo ""
echo "编辑 Mac Mini 上的配置文件："
echo "  nano /Users/wzy/01-note/dashboard-ocmonitor/dashboard-config.json"
echo ""
echo "添加以下配置："
echo "{"
echo "  \"devices\": ["
echo "    {"
echo "      \"id\": \"local\","
echo "      \"name\": \"Mac Mini\","
echo "      \"url\": \"local\","
echo "      \"enabled\": true"
echo "    },"
echo "    {"
echo "      \"id\": \"macbook-01\","
echo "      \"name\": \"MacBook Pro\","
echo "      \"url\": \"http://$MACBOOK_IP:38002\","
echo "      \"enabled\": true"
echo "    }"
echo "  ]"
echo "}"
echo ""
echo "然后在 Mac Mini 上重启服务："
echo "  cd /Users/wzy/01-note/dashboard-ocmonitor"
echo "  pkill -f \"python3 app.py\""
echo "  nohup python3 app.py > logs/app.log 2>&1 &"
