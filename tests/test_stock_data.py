#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正股数据端点测试

测试 /api/stock-data 接口
"""


def test_stock_data_endpoint_returns_success(client):
    """
    测试正股数据端点返回成功

    期望:
    - HTTP状态码 200
    - success 为 True
    - 包含 spot 和 ma 字段
    """
    response = client.get('/api/stock-data')

    assert response.status_code == 200
    assert response.json['success'] is True
    assert 'spot' in response.json
    assert 'ma' in response.json


def test_stock_data_spot_has_required_fields(client):
    """
    测试正股行情数据包含必需字段

    必需字段:
    - 正股代码
    - 正股名称
    - 当前股价
    - PB
    """
    required_fields = ['正股代码', '正股名称', '当前股价', 'PB']

    response = client.get('/api/stock-data')
    spot_list = response.json['spot']

    if spot_list:
        first_item = spot_list[0]
        for field in required_fields:
            assert field in first_item, f"字段 {field} 应该存在"


def test_stock_data_ma_has_required_fields(client):
    """
    测试均线数据包含必需字段

    必需字段:
    - 正股代码
    - MA5
    - MA10
    - MA20
    """
    required_fields = ['正股代码', 'MA5', 'MA10', 'MA20']

    response = client.get('/api/stock-data')
    ma_list = response.json['ma']

    if ma_list:
        first_item = ma_list[0]
        for field in required_fields:
            assert field in first_item, f"字段 {field} 应该存在"


def test_stock_data_ma_is_limited(client):
    """
    测试均线数据有数量限制

    期望:
    - MA数据不超过100条（避免超时）
    """
    response = client.get('/api/stock-data')
    ma_list = response.json['ma']

    assert len(ma_list) <= 100, "MA数据应该限制在100条以内"
