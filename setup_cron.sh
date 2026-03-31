#!/bin/bash
# 可转债每日推送定时任务设置脚本

# 获取当前目录
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "设置可转债每日推送定时任务..."
echo "项目目录: $PROJECT_DIR"

# 创建输出目录
mkdir -p "$PROJECT_DIR/output"
mkdir -p "$PROJECT_DIR/logs"

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi

# 检查虚拟环境
if [ -d "$PROJECT_DIR/venv" ]; then
    PYTHON="$PROJECT_DIR/venv/bin/python3"
else
    PYTHON="python3"
fi

# 安装依赖
echo "安装依赖..."
$PYTHON -m pip install -r "$PROJECT_DIR/requirements.txt" -q

# 创建环境变量配置模板
if [ ! -f "$PROJECT_DIR/.env" ]; then
    cat > "$PROJECT_DIR/.env" << 'EOF'
# 远程服务器配置
REMOTE_HOST=47.84.177.254
REMOTE_USER=root
REMOTE_PASSWORD=your_password_here
REMOTE_PATH=/var/www/html/cb_data
REMOTE_PORT=22

# 本地 API 地址
API_BASE_URL=http://localhost:5001
EOF
    echo "已创建 .env 配置文件模板，请编辑配置"
fi

# 创建定时任务脚本
CRON_SCRIPT="$PROJECT_DIR/run_daily.sh"
cat > "$CRON_SCRIPT" << EOF
#!/bin/bash
# 可转债每日推送执行脚本

cd "$PROJECT_DIR"

# 加载环境变量
if [ -f .env ]; then
    export \$(grep -v '^#' .env | xargs)
fi

# 使用虚拟环境
if [ -d venv ]; then
    source venv/bin/activate
fi

# 日志文件
LOG_FILE="logs/daily_\$(date +%Y%m%d).log"
mkdir -p logs

echo "========================================" >> "\$LOG_FILE"
echo "开始执行: \$(date)" >> "\$LOG_FILE"

# 执行推送
python3 daily_push.py >> "\$LOG_FILE" 2>&1
RESULT=\$?

echo "执行结束: \$(date), 退出码: \$RESULT" >> "\$LOG_FILE"
echo "" >> "\$LOG_FILE"

exit \$RESULT
EOF

chmod +x "$CRON_SCRIPT"

echo ""
echo "定时任务设置选项:"
echo ""
echo "1. 使用 crontab (推荐)"
echo "   每天 9:30 执行:"
echo "   30 9 * * 1-5 $CRON_SCRIPT"
echo ""
echo "   添加到 crontab 的命令:"
echo "   (crontab -l 2>/dev/null; echo '30 9 * * 1-5 $CRON_SCRIPT') | crontab -"
echo ""
echo "2. 使用 launchd (macOS)"
echo "   创建 plist 文件到 ~/Library/LaunchAgents/"
echo ""
echo "3. 手动测试"
echo "   运行: $CRON_SCRIPT"
echo ""
echo "配置文件: $PROJECT_DIR/.env"
echo "请编辑 .env 文件设置远程服务器密码"
