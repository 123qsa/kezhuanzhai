#!/bin/bash
# -*- coding: utf-8 -*-
"""
云服务器定时任务设置脚本

在云服务器上执行，设置每天 9:30 自动采集数据。
"""

set -e

echo "========================================"
echo "设置可转债定时任务"
echo "========================================"

PROJECT_DIR="/opt/kezhuanzhai"
CRON_JOB="30 9 * * 1-5 $PROJECT_DIR/run_daily.sh >> $PROJECT_DIR/logs/cron.log 2>&1"

# 检查当前 crontab
echo ""
echo "当前定时任务:"
crontab -l 2>/dev/null || echo "(无)"

echo ""
echo "添加新的定时任务..."

# 备份当前 crontab
crontab -l 2>/dev/null > /tmp/crontab_backup.txt || true

# 添加新任务（避免重复）
if ! grep -q "run_daily.sh" /tmp/crontab_backup.txt 2>/dev/null; then
    echo "" >> /tmp/crontab_backup.txt
    echo "# 可转债每日数据采集 - 工作日 9:30" >> /tmp/crontab_backup.txt
    echo "$CRON_JOB" >> /tmp/crontab_backup.txt
    crontab /tmp/crontab_backup.txt
    echo "✓ 定时任务已添加"
else
    echo "定时任务已存在，跳过"
fi

echo ""
echo "更新后的定时任务:"
crontab -l | tail -5

echo ""
echo "========================================"
echo "定时任务设置完成"
echo "========================================"
echo ""
echo "数据将在工作日 9:30 自动采集"
echo "日志位置: $PROJECT_DIR/logs/"
echo ""
echo "手动测试: $PROJECT_DIR/run_daily.sh"
echo ""
