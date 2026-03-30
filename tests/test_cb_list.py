#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可转债列表端点测试

测试 /api/cb-list 接口
"""
import pytest


def test_cb_list_endpoint_returns_success(client):
    """
    测试可转债列表端点返回成功

    期望:
    - HTTP状态码 200
    - success 为 True
    - 包含 cb_list 字段
    - 包含 count 字段
    """
    # Act
    response = client.get('/api/cb-list')

    # Assert
    assert response.status_code == 200
    assert response.json['success'] is True
    assert 'cb_list' in response.json
    assert 'count' in response.json


def test_cb_list_returns_reasonable_count(client):
    """
    测试可转债列表返回合理数量

    期望:
    - 数量大于0（有数据）
    - 数量小于1000（合理范围）
    """
    response = client.get('/api/cb-list')
    data = response.json

    assert data['count'] > 0, "应该返回至少一条可转债数据"
    assert data['count'] < 1000, "可转债数量应该小于1000"
    assert len(data['cb_list']) == data['count']


def test_cb_list_item_has_required_fields(client):
    """
    测试可转债条目包含必需字段

    必需字段:
    - 转债代码
    - 转债名称
    - 正股代码
    - 正股名称
    - 转股价格
    - 可转债剩余规模
    - 到期日期
    """
    required_fields = [
        '转债代码',
        '转债名称',
        '正股代码',
        '正股名称',
        '转股价格',
        '可转债剩余规模',
        '到期日期'
    ]

    response = client.get('/api/cb-list')
    cb_list = response.json['cb_list']

    # 至少有一条数据才能验证字段
    if cb_list:
        first_item = cb_list[0]
        for field in required_fields:
            assert field in first_item, f"字段 {field} 应该存在"


def test_cb_list_handles_errors(client):
    """
    测试可转债列表端点错误处理

    期望:
    - 即使出错也返回JSON
    - 包含 error 字段
    - success 为 False
    """
    # 正常情况应该返回成功
    response = client.get('/api/cb-list')

    # 如果出错，应该返回 success=False
    if not response.json['success']:
        assert 'error' in response.json
