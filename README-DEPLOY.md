# 可转债每日统计系统 - 完整部署指南

## 系统架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   n8n       │────▶│ Python API  │────▶│  AkShare    │
│  工作流引擎  │     │  数据获取    │     │  数据源     │
└──────┬──────┘     └─────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐
│ Frontend API│────▶ 前端展示页面
│  数据接收    │
└─────────────┘
```

## 快速启动（Docker 方式 - 推荐）

### 1. 确保 Docker 和 Docker Compose 已安装

```bash
docker --version
docker-compose --version
```

### 2. 启动所有服务

```bash
cd /Users/ray/Desktop/project/kezhuanzhai
docker-compose up -d
```

### 3. 等待服务启动（约 30 秒）

```bash
# 查看日志
docker-compose logs -f

# 按 Ctrl+C 退出日志查看
```

### 4. 访问服务

| 服务 | 地址 | 说明 |
|------|------|------|
| n8n | http://localhost:5678 | 工作流引擎 (admin/admin123) |
| 前端展示 | http://localhost:3000 | 可转债数据展示 |
| Python API | http://localhost:5000 | 数据获取服务 |

### 5. 导入工作流

1. 登录 n8n: http://localhost:5678
2. 点击左侧 **Workflows**
3. 点击 **Import from File**
4. 选择 `workflow-v2.json`
5. 点击 **Save**

### 6. 测试工作流

1. 在工作流页面点击 **Execute Workflow**
2. 等待执行完成
3. 访问 http://localhost:3000 查看数据

---

## 手动启动方式（开发调试）

### 启动前端 API（已运行）

```bash
cd frontend-api
npm start
```

服务运行在 http://localhost:3000

### 启动 Python API

```bash
# 安装依赖
pip install akshare flask pandas

# 启动服务
python python_api.py
```

服务运行在 http://localhost:5000

### 配置 n8n 工作流

如果使用手动方式，需要修改工作流中的 URL：

- `http://python-runner:5000` → `http://localhost:5000`
- `http://frontend-api:3000` → `http://localhost:3000`

---

## 目录结构

```
kezhuanzhai/
├── docker-compose.yml          # Docker 编排配置
├── Dockerfile.python           # Python 服务镜像
├── python_api.py               # Python API 服务
├── workflow-v2.json            # n8n 工作流配置
├── README-DEPLOY.md            # 本文件
│
├── n8n_scripts/                # Python 数据脚本
│   ├── check_trade_day.py
│   ├── get_cb_list.py
│   ├── get_stock_data.py
│   ├── get_controller.py
│   ├── get_finance.py
│   └── 可转债工作流.json
│
└── frontend-api/               # 前端 API + 展示
    ├── server.js
    ├── index.html
    ├── package.json
    └── Dockerfile
```

---

## 常用命令

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 查看日志
docker-compose logs -f

# 重启单个服务
docker-compose restart n8n
docker-compose restart python-runner
docker-compose restart frontend-api

# 进入容器调试
docker-compose exec n8n /bin/sh
docker-compose exec python-runner /bin/bash
```

---

## 故障排查

### 1. n8n 无法访问

```bash
# 检查容器状态
docker-compose ps

# 查看 n8n 日志
docker-compose logs n8n

# 检查端口是否被占用
lsof -i :5678
```

### 2. Python API 无响应

```bash
# 检查 Python 服务
docker-compose logs python-runner

# 测试 API
curl http://localhost:5000/health
```

### 3. 前端没有数据

```bash
# 检查前端 API
curl http://localhost:3000/api/cb-data

# 手动推送测试数据
./test_push.sh
```

### 4. 工作流执行失败

1. 在 n8n UI 中查看执行历史
2. 检查节点错误信息
3. 确认 Python API 可访问

---

## 自定义配置

### 修改定时时间

在 n8n 工作流的 **Cron触发** 节点中修改：

```
工作日 9:30  →  field: weekday=1-5, hour=9, minute=30
工作日 15:30 →  field: weekday=1-5, hour=15, minute=30
```

### 修改数据接收地址

在 **HTTP推送前端** 节点中修改 URL：

```
http://frontend-api:3000/api/cb-data
```

### 添加认证

如需添加 API Key 认证，修改 `frontend-api/server.js`：

```javascript
// 添加认证中间件
app.use((req, res, next) => {
  const apiKey = req.headers['x-api-key'];
  if (apiKey !== process.env.API_KEY) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  next();
});
```

---

## 生产环境建议

1. **使用反向代理**（Nginx/Caddy）
2. **启用 HTTPS**
3. **配置数据库持久化**（PostgreSQL 已配置）
4. **设置备份策略**
5. **配置监控告警**

---

## 系统要求

- Docker 20.10+
- Docker Compose 2.0+
- 内存：4GB+
- 磁盘：10GB+
