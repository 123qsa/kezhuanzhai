#!/bin/bash
# 前端部署脚本 - 部署到云服务器 Nginx

set -e

REMOTE_HOST="${REMOTE_HOST:-47.84.177.254}"
REMOTE_USER="${REMOTE_USER:-root}"
REMOTE_DIR="/var/www/html/cb_data"

echo "========================================"
echo "前端页面部署"
echo "========================================"

if [ -z "$REMOTE_PASSWORD" ]; then
    echo "错误: 请设置 REMOTE_PASSWORD 环境变量"
    exit 1
fi

echo ""
echo "[1/3] 创建远程目录..."
sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_DIR"

echo ""
echo "[2/3] 上传前端文件..."
sshpass -p "$REMOTE_PASSWORD" rsync -avz \
    -e "ssh -o StrictHostKeyChecking=no" \
    index.html "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"

echo ""
echo "[3/3] 更新 Nginx 配置..."
sshpass -p "$REMOTE_PASSWORD" scp -o StrictHostKeyChecking=no nginx.conf "$REMOTE_USER@$REMOTE_HOST:/etc/nginx/sites-available/cb_data"

sshpass -p "$REMOTE_PASSWORD" ssh -o StrictHostKeyChecking=no "$REMOTE_USER@$REMOTE_HOST" "
    ln -sf /etc/nginx/sites-available/cb_data /etc/nginx/sites-enabled/ 2>/dev/null || true
    nginx -t && nginx -s reload
"

echo ""
echo "========================================"
echo "部署完成！"
echo "========================================"
echo ""
echo "访问地址: http://$REMOTE_HOST"
echo ""
