// 前端 API 测试
// 使用 Jest + Supertest

const request = require('supertest');
const app = require('./server');

describe('前端 API 测试', () => {
  describe('GET /', () => {
    test('应该返回前端页面', async () => {
      const response = await request(app)
        .get('/')
        .expect(200);

      expect(response.text).toContain('<!DOCTYPE html>');
      expect(response.text).toContain('可转债每日统计');
    });
  });

  describe('GET /api/cb-data', () => {
    test('应该返回最新数据', async () => {
      const response = await request(app)
        .get('/api/cb-data')
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body).toHaveProperty('data');
      expect(response.body).toHaveProperty('count');
      expect(response.body).toHaveProperty('date');
      expect(response.body).toHaveProperty('csv');
    });

    test('空数据时返回空数组', async () => {
      const response = await request(app)
        .get('/api/cb-data')
        .expect(200);

      expect(Array.isArray(response.body.data)).toBe(true);
    });
  });

  describe('POST /api/cb-data', () => {
    test('应该接收并存储数据', async () => {
      const testData = [
        {
          正股代码: '000001',
          正股名称: '平安银行',
          转债名称: '平银转债',
          当前股价: 10.5,
          PB: 1.2
        }
      ];

      const response = await request(app)
        .post('/api/cb-data')
        .send({
          data: JSON.stringify(testData),
          csv: '正股代码,正股名称\n000001,平安银行',
          count: 1,
          date: '2026-03-29'
        })
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body.message).toContain('成功接收');
    });

    test('应该处理大数据量', async () => {
      // 生成50条测试数据
      const testData = Array.from({ length: 50 }, (_, i) => ({
        正股代码: `000${i.toString().padStart(3, '0')}`,
        正股名称: `测试股票${i}`,
        转债名称: `测试转债${i}`,
        当前股价: 10 + i,
        PB: 1.5
      }));

      const response = await request(app)
        .post('/api/cb-data')
        .send({
          data: JSON.stringify(testData),
          csv: '正股代码,正股名称\n000001,测试',
          count: 50,
          date: '2026-03-29'
        })
        .expect(200);

      expect(response.body).toHaveProperty('success', true);
      expect(response.body.message).toContain('50');
    });

    test('应该处理无效的JSON', async () => {
      const response = await request(app)
        .post('/api/cb-data')
        .send({
          data: 'invalid json',
          count: 0
        })
        .expect(400);

      expect(response.body).toHaveProperty('success', false);
      expect(response.body).toHaveProperty('error');
    });
  });

  describe('GET /api/cb-data/download', () => {
    test('应该返回CSV文件', async () => {
      // 先写入一些数据
      await request(app)
        .post('/api/cb-data')
        .send({
          data: JSON.stringify([{ 正股代码: '000001', 正股名称: '测试' }]),
          csv: '正股代码,正股名称\n000001,测试',
          count: 1,
          date: '2026-03-29'
        });

      const response = await request(app)
        .get('/api/cb-data/download')
        .expect(200);

      expect(response.headers['content-type']).toContain('text/csv');
      expect(response.headers['content-disposition']).toContain('attachment');
    });
  });

  describe('CORS 支持', () => {
    test('应该允许跨域请求', async () => {
      const response = await request(app)
        .get('/api/cb-data')
        .set('Origin', 'http://example.com')
        .expect(200);

      expect(response.headers['access-control-allow-origin']).toBe('*');
    });
  });
});