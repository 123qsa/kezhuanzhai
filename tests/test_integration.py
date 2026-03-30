#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
集成测试

测试整个数据流程
"""


def test_data_consistency_across_endpoints(client):
    """
    测试各端点数据一致性

    验证:
    - 可转债列表的正股代码应该在股东数据中存在
    - 可转债列表的正股代码应该在财务数据中存在
    """
    # 获取所有数据
    cb_response = client.get('/api/cb-list')
    controller_response = client.get('/api/controller')
    finance_response = client.get('/api/finance')

    cb_list = cb_response.json['cb_list']
    controller_data = controller_response.json['controller_data']
    finance_data = finance_response.json['finance_data']

    # 提取正股代码
    cb_stock_codes = {item['正股代码'] for item in cb_list}
    controller_stock_codes = {item['正股代码'] for item in controller_data}
    finance_stock_codes = {item['正股代码'] for item in finance_data}

    # 验证股东数据包含可转债的正股代码（至少前10个）
    sample_codes = list(cb_stock_codes)[:10]
    for code in sample_codes:
        assert code in controller_stock_codes, f"正股代码 {code} 应该在股东数据中"

    # 验证财务数据包含可转债的正股代码（至少前10个）
    for code in sample_codes:
        assert code in finance_stock_codes, f"正股代码 {code} 应该在财务数据中"


def test_data_flow_simulation(client):
    """
    模拟完整数据流程测试

    流程:
    1. 检查是否是交易日
    2. 获取可转债列表
    3. 获取正股数据
    4. 获取股东数据
    5. 获取财务数据
    6. 数据合并
    """
    # 1. 检查交易日
    trade_day_response = client.get('/api/check-trade-day')
    assert trade_day_response.json['success'] is True

    # 2. 获取可转债列表
    cb_response = client.get('/api/cb-list')
    assert cb_response.json['success'] is True
    assert cb_response.json['count'] > 0

    # 3. 获取正股数据
    stock_response = client.get('/api/stock-data')
    assert stock_response.json['success'] is True
    assert len(stock_response.json['spot']) > 0

    # 4. 获取股东数据
    controller_response = client.get('/api/controller')
    assert controller_response.json['success'] is True

    # 5. 获取财务数据
    finance_response = client.get('/api/finance')
    assert finance_response.json['success'] is True

    # 6. 验证数据可以合并
    cb_list = cb_response.json['cb_list']
    spot_map = {s['正股代码']: s for s in stock_response.json['spot']}

    # 验证至少前5条可转债可以找到对应的正股数据
    for cb in cb_list[:5]:
        stock_code = cb['正股代码']
        assert stock_code in spot_map, f"正股代码 {stock_code} 应该在正股数据中"
