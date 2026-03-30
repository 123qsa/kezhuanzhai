#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
交易日检查端点测试

测试 /api/check-trade-day 接口
"""


def test_check_trade_day_returns_success(client):
    """
    测试交易日检查端点返回成功

    期望:
    - HTTP状态码 200
    - 包含 is_trade_day 字段
    - 包含 today 字段
    - 包含 success 字段
    """
    response = client.get('/api/check-trade-day')

    assert response.status_code == 200
    assert 'is_trade_day' in response.json
    assert 'today' in response.json
    assert 'success' in response.json


def test_check_trade_day_returns_boolean(client):
    """
    测试 is_trade_day 返回布尔值
    """
    response = client.get('/api/check-trade-day')
    is_trade_day = response.json['is_trade_day']

    assert isinstance(is_trade_day, bool), "is_trade_day 应该是布尔值"


def test_check_trade_day_returns_date_string(client):
    """
    测试 today 返回日期字符串格式 YYYYMMDD
    """
    response = client.get('/api/check-trade-day')
    today = response.json['today']

    assert isinstance(today, str), "today 应该是字符串"
    assert len(today) == 8, "today 应该是8位数字 (YYYYMMDD)"
    assert today.isdigit(), "today 应该只包含数字"
