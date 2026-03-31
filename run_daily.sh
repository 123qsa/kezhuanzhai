#!/bin/bash
# -*- coding: utf-8 -*-
"""
云服务器定时任务脚本

每天早上执行数据采集并生成 CSV。
不需要推送到远程，因为已经在服务器上。

用法:
    添加到 crontab: 30 9 * * 1-5 /opt/kezhuanzhai/run_daily.sh
"""

set -e

PROJECT_DIR="/opt/kezhuanzhai"
LOG_FILE="$PROJECT_DIR/logs/daily_$(date +%Y%m%d).log"
NGINX_DIR="/var/www/html/cb_data"

# 创建日志目录
mkdir -p "$PROJECT_DIR/logs"
mkdir -p "$NGINX_DIR"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========================================"
log "开始执行可转债每日数据采集"
log "========================================"

cd "$PROJECT_DIR"

# 检查 Docker 容器是否运行
if ! docker-compose ps | grep -q "kezhuanzhai-api.*Up"; then
    log "错误: API 容器未运行，尝试启动..."
    docker-compose up -d
    sleep 5
fi

# 在容器内执行数据采集
docker-compose exec -T cb-api python daily_push.py --skip-trade-check --skip-validation >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    log "✓ 数据采集成功"

    # 复制 CSV 到 Nginx 目录
    LATEST_CSV=$(ls -t output/cb_data_*.csv 2>/dev/null | head -1)
    if [ -n "$LATEST_CSV" ]; then
        cp "$LATEST_CSV" "$NGINX_DIR/"
        log "✓ CSV 文件已复制到 Nginx 目录: $(basename $LATEST_CSV)"
        log "访问地址: http://$(hostname -I | awk '{print $1}')/cb_data/$(basename $LATEST_CSV)"
    else
        log "警告: 未找到生成的 CSV 文件"
    fi
else
    log "✗ 数据采集失败，退出码: $EXIT_CODE"
fi

log "========================================"
log "执行结束"
log "========================================"

exit $EXIT_CODE
