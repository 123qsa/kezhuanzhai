#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
财务数据端点测试

测试 /api/finance 接口
"""


def test_finance_endpoint_returns_success(client):
    """
    测试财务数据端点返回成功

    期望:
    - HTTP状态码 200
    - success 为 True
    - 包含 finance_data 字段
    """
    response = client.get('/api/finance')

    assert response.status_code == 200
    assert response.json['success'] is True
    assert 'finance_data' in response.json


def test_finance_data_has_required_fields(client):
    """
    测试财务数据包含必需字段

    必需字段:
    - 正股代码
    - 期末现金余额
    - 货币资金
    """
    required_fields = ['正股代码', '期末现金余额', '货币资金']

    response = client.get('/api/finance')
    finance_list = response.json['finance_data']

    if finance_list:
        first_item = finance_list[0]
        for field in required_fields:
            assert field in first_item, f"字段 {field} 应该存在"


def test_finance_matches_cb_list_count(client):
    """
    测试财务数据数量与可转债列表匹配

    期望:
    - 财务数据数量应该接近可转债列表数量
    """
    # 获取可转债列表数量
    cb_response = client.get('/api/cb-list')
    cb_count = cb_response.json['count']

    # 获取财务数据数量
    finance_response = client.get('/api/finance')
    finance_count = len(finance_response.json['finance_data'])

    # 允许少量差异
    assert abs(cb_count - finance_count) <= 10, \
        f"财务数据数量({finance_count})应与可转债数量({cb_count})接近"
