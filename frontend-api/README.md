# 可转债数据前端展示

## 文件结构

```
frontend-api/
├── server.js          # Express API 服务端
├── index.html         # 前端展示页面
├── package.json       # 依赖配置
└── README.md          # 使用说明
```

## 快速开始

### 1. 安装依赖

```bash
cd frontend-api
npm install
```

### 2. 启动服务

```bash
# 开发模式（带热重载）
npm run dev

# 生产模式
npm start
```

服务将启动在 http://localhost:3000

### 3. 配置 n8n HTTP 节点

在 n8n 的 `HTTP推送数据` 节点中：

- **Method**: POST
- **URL**: `http://your-server-ip:3000/api/cb-data`
- **Body Content Type**: Form-Data
- **Parameters**:
  - `data`: `={{ JSON.stringify($json.merged_data) }}`
  - `csv`: `={{ $json.csv_content }}`
  - `count`: `={{ $json.count }}`
  - `date`: `={{ new Date().toISOString() }}`

### 4. 访问前端

打开浏览器访问: http://localhost:3000

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/cb-data` | POST | 接收 n8n 推送的数据 |
| `/api/cb-data` | GET | 获取最新数据 |
| `/api/cb-data/download` | GET | 下载 CSV 文件 |

## 功能特性

- ✅ 自动接收 n8n 推送的数据
- ✅ 实时统计展示（总数、平均PB、强赎预警、股东类型）
- ✅ 表格展示所有可转债数据
- ✅ 强赎预警高亮显示
- ✅ 支持搜索过滤
- ✅ 自动刷新（30秒）
- ✅ CSV 下载

## 生产环境部署

### 使用 PM2

```bash
npm install -g pm2
pm2 start server.js --name cb-data-api
pm2 save
pm2 startup
```

### 使用 Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
EXPOSE 3000
CMD ["node", "server.js"]
```

```bash
docker build -t cb-data-frontend .
docker run -d -p 3000:3000 cb-data-frontend
```

## 自定义配置

可通过环境变量配置：

```bash
PORT=8080              # 服务端口号
API_ENDPOINT=http://... # n8n 推送地址（用于验证）
```
