#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康检查端点测试

RED: 先写测试，预期失败
GREEN: 实现最小代码让测试通过
REFACTOR: 清理代码
"""


def test_health_endpoint_returns_ok(client):
    """
    RED: 测试健康检查端点返回状态ok

    期望:
    - HTTP状态码 200
    - 返回JSON包含 status: "ok"
    """
    # Act
    response = client.get('/health')

    # Assert
    assert response.status_code == 200
    assert response.json['status'] == 'ok'


def test_health_endpoint_returns_json(client):
    """
    测试健康检查端点返回正确Content-Type

    期望:
    - Content-Type 为 application/json
    """
    response = client.get('/health')

    assert response.content_type == 'application/json'
    assert 'status' in response.json
