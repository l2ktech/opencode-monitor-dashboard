#!/bin/bash

set -e

PROJECT_DIR="${1:-./}"
REPO_URL="${2:-}"
BRANCH="${3:-main}"

cd "$PROJECT_DIR" || exit 1

echo "正在同步代码..."

if [ -n "$REPO_URL" ]; then
    if [ -d ".git" ]; then
        echo "从远程仓库拉取最新代码..."
        git pull origin "$BRANCH"
    else
        echo "克隆仓库..."
        git clone "$REPO_URL" .
    fi
else
    if [ -d ".git" ]; then
        echo "从默认远程仓库拉取最新代码..."
        git pull
    else
        echo "错误: 不是 git 仓库且未指定仓库地址"
        exit 1
    fi
fi

echo ""
echo "检查是否需要修复 app.py..."
if [ -f "fix-app.py" ]; then
    echo "运行修复脚本..."
    bash fix-app.py
else
    echo "未找到 fix-app.py 脚本"
fi

echo ""
echo "同步完成！"
echo "如需重启服务，请运行:"
echo "  pkill -f 'python.*app.py' && nohup python3 app.py &"