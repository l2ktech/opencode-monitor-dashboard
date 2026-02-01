#!/bin/bash

echo "正在扫描局域网中的设备..."
echo "Mac Mini IP: $(ipconfig getifaddr en0)"
echo ""
echo "尝试发现其他设备："
echo ""

for i in {1..20}; do
    ip="192.168.1.$i"
    if [ "$ip" != "192.168.1.4" ]; then
        if ping -c 1 -W 1 $ip > /dev/null 2>&1; then
            echo "✅ 发现设备: $ip"
            
            if curl -s --connect-timeout 2 http://$ip:38002/api/sessions > /dev/null 2>&1; then
                echo "   🎯 此设备运行 Dashboard (端口 38002)"
                echo "   测试 API: curl http://$ip:38002/api/sessions"
            fi
        fi
    fi
done

echo ""
echo "扫描完成"
