// 可转债数据接收 API 示例
// 使用 Express.js + multer 处理 multipart/form-data

const express = require('express');
const multer = require('multer');
const cors = require('cors');
const path = require('path');

const app = express();
const upload = multer({ storage: multer.memoryStorage() });

// 启用 CORS（允许 n8n 访问）
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// 静态文件服务 - 提供前端页面
app.use(express.static(path.join(__dirname)));

// 内存存储最新数据（生产环境建议用数据库）
let latestData = {
  date: null,
  count: 0,
  data: [],
  csv: ''
};

/**
 * POST /api/cb-data
 * 接收 n8n 推送的可转债数据
 */
app.post('/api/cb-data', upload.none(), (req, res) => {
  try {
    const { data, csv, count, date } = req.body;

    // 解析 JSON 数据
    const parsedData = JSON.parse(data || '[]');

    // 存储数据
    latestData = {
      date: date || new Date().toISOString(),
      count: parseInt(count) || 0,
      data: parsedData,
      csv: csv || ''
    };

    console.log(`[${new Date().toLocaleString()}] 收到可转债数据: ${latestData.count} 条`);

    res.json({
      success: true,
      message: `成功接收 ${latestData.count} 条数据`,
      receivedAt: new Date().toISOString()
    });
  } catch (error) {
    console.error('接收数据失败:', error);
    res.status(400).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * GET /api/cb-data
 * 前端获取最新数据
 */
app.get('/api/cb-data', (req, res) => {
  res.json({
    success: true,
    ...latestData
  });
});

/**
 * GET /api/cb-data/download
 * 下载 CSV 文件
 */
app.get('/api/cb-data/download', (req, res) => {
  const date = new Date().toISOString().split('T')[0];
  const filename = `kezhuanzhai_${date}.csv`;
  res.setHeader('Content-Type', 'text/csv; charset=utf-8');
  res.setHeader('Content-Disposition', `attachment; filename="${filename}"; filename*=UTF-8''${encodeURIComponent(filename)}`);
  res.send(latestData.csv);
});

/**
 * GET /
 * 根路径返回前端页面
 */
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

// 启动服务器
const PORT = process.env.PORT || 3000;

// 如果不是测试环境，启动服务器
if (process.env.NODE_ENV !== 'test') {
  app.listen(PORT, '0.0.0.0', () => {
    console.log(`可转债数据 API 已启动: http://0.0.0.0:${PORT}`);
    console.log(`POST /api/cb-data    - 接收 n8n 数据推送`);
    console.log(`GET  /api/cb-data    - 获取最新数据`);
    console.log(`GET  /api/cb-data/download - 下载 CSV`);
  });
}

// 导出 app 供测试使用
module.exports = app;
