#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股东信息端点测试

测试 /api/controller 接口
"""


def test_controller_endpoint_returns_success(client):
    """
    测试股东信息端点返回成功

    期望:
    - HTTP状态码 200
    - success 为 True
    - 包含 controller_data 字段
    """
    response = client.get('/api/controller')

    assert response.status_code == 200
    assert response.json['success'] is True
    assert 'controller_data' in response.json


def test_controller_data_has_required_fields(client):
    """
    测试股东数据包含必需字段

    必需字段:
    - 正股代码
    - 大股东类型
    - 实际控制人
    - 实控人类型
    """
    required_fields = ['正股代码', '大股东类型', '实际控制人', '实控人类型']

    response = client.get('/api/controller')
    controller_list = response.json['controller_data']

    if controller_list:
        first_item = controller_list[0]
        for field in required_fields:
            assert field in first_item, f"字段 {field} 应该存在"


def test_controller_matches_cb_list_count(client):
    """
    测试股东数据数量与可转债列表匹配

    期望:
    - 股东数据数量应该接近可转债列表数量
    """
    # 获取可转债列表数量
    cb_response = client.get('/api/cb-list')
    cb_count = cb_response.json['count']

    # 获取股东数据数量
    controller_response = client.get('/api/controller')
    controller_count = len(controller_response.json['controller_data'])

    # 允许少量差异（有些股票可能没有股东数据）
    assert abs(cb_count - controller_count) <= 10, \
        f"股东数据数量({controller_count})应与可转债数量({cb_count})接近"
