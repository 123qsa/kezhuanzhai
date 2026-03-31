#!/bin/bash
# 云服务器部署脚本
# 在本地执行，自动部署到云服务器

set -e

REMOTE_HOST="${REMOTE_HOST:-47.84.177.254}"
REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_DIR="/opt/kezhuanzhai"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================"
echo "可转债系统 - 云服务器部署"
echo "========================================"

if [ -z "$REMOTE_PASSWORD" ]; then
    echo "错误: 请设置 REMOTE_PASSWORD 环境变量"
    exit 1
fi

echo ""
echo "[1/6] 同步代码到云服务器..."
sshpass -p "$REMOTE_PASSWORD" rsync -avz \
    -e "ssh -o StrictHostKeyChecking=no" \
    --exclude='.git' \
    --exclude='venv' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='output' \
    --exclude='logs' \
    --exclude='.env' \
    ./ "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

echo ""
echo "[2/6] 创建数据目录..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_DIR/output $REMOTE_DIR/logs"

echo ""
echo "[3/6] 构建并启动 Docker 容器..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR && docker-compose down 2>/dev/null; docker-compose build --no-cache && docker-compose up -d"

echo ""
echo "[4/6] 等待服务启动..."
sleep 10

echo ""
echo "[5/6] 检查服务状态..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR && docker-compose ps"

echo ""
echo "[6/6] 测试 API 接口..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "curl -s http://localhost:5001/health || echo '服务尚未就绪'"

echo ""
echo "========================================"
echo "部署完成！"
echo "========================================"
echo ""
echo "API 地址: http://$REMOTE_HOST:5001"
echo "健康检查: http://$REMOTE_HOST:5001/health"
echo ""
