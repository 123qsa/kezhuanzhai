# 可转债系统测试指南

## Python API 测试

### 安装依赖

```bash
cd /Users/ray/Desktop/project/kezhuanzhai
python3 -m venv venv
source venv/bin/activate
pip install -r tests/requirements-test.txt
```

### 运行测试

```bash
# 运行所有测试
python3 -m pytest tests/ -v

# 运行特定测试文件
python3 -m pytest tests/test_health.py -v
python3 -m pytest tests/test_cb_list.py -v

# 生成覆盖率报告
python3 -m pytest tests/ --cov=python_api --cov-report=html
```

### 测试文件说明

| 测试文件 | 测试内容 | 测试数量 |
|---------|---------|---------|
| `test_health.py` | 健康检查端点 | 2 |
| `test_cb_list.py` | 可转债列表端点 | 4 |
| `test_stock_data.py` | 正股数据端点 | 4 |
| `test_controller.py` | 股东信息端点 | 3 |
| `test_finance.py` | 财务数据端点 | 3 |
| `test_check_trade_day.py` | 交易日检查端点 | 3 |
| `test_integration.py` | 集成测试 | 2 |
| **合计** | | **21** |

---

## 前端 API 测试

### 安装依赖

```bash
cd /Users/ray/Desktop/project/kezhuanzhai/frontend-api
npm install
```

### 运行测试

```bash
# 运行测试
npm test

# 持续监听模式
npm test -- --watch

# 只运行测试，不生成覆盖率
npm test -- --coverage=false
```

### 测试文件说明

| 测试套件 | 测试内容 | 测试数量 |
|---------|---------|---------|
| `GET /` | 前端页面返回 | 1 |
| `GET /api/cb-data` | 数据获取 | 2 |
| `POST /api/cb-data` | 数据接收 | 3 |
| `GET /api/cb-data/download` | CSV下载 | 1 |
| `CORS` | 跨域支持 | 1 |
| **合计** | | **8** |

---

## TDD 开发流程

### 1. RED - 编写失败的测试

```python
def test_new_feature():
    # 编写测试，预期失败
    response = client.get('/api/new-feature')
    assert response.status_code == 200
```

### 2. GREEN - 实现最小代码

```python
@app.route('/api/new-feature')
def new_feature():
    return jsonify({"status": "ok"})
```

### 3. REFACTOR - 清理代码

优化实现，保持测试通过。

---

## 测试结果

### Python API 测试结果

```
============================= test session starts ==============================
platform darwin -- Python 3.14.0, pytest-9.0.2, pluggy-1.6.0
collected 21 items

tests/test_cb_list.py ....
tests/test_check_trade_day.py ...
tests/test_controller.py ...
tests/test_finance.py ...
tests/test_health.py ..
tests/test_integration.py ..
tests/test_stock_data.py ....

================== 21 passed in 543.14s ==================
```

### 前端 API 测试结果

```
PASS ./server.test.js
  前端 API 测试
    GET /
      ✓ 应该返回前端页面
    GET /api/cb-data
      ✓ 应该返回最新数据
      ✓ 空数据时返回空数组
    POST /api/cb-data
      ✓ 应该接收并存储数据
      ✓ 应该处理大数据量
      ✓ 应该处理无效的JSON
    GET /api/cb-data/download
      ✓ 应该返回CSV文件
    CORS 支持
      ✓ 应该允许跨域请求

Test Suites: 1 passed, 1 total
Tests:       8 passed, 8 total
```

---

## 持续集成建议

### GitHub Actions 配置示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  python-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r tests/requirements-test.txt
      - name: Run tests
        run: |
          python3 -m pytest tests/ -v

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: |
          cd frontend-api
          npm install
      - name: Run tests
        run: |
          cd frontend-api
          npm test
```
