#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日数据验证 - n8n 集成版

简化版验证程序，用于 n8n 工作流中作为验证节点。
返回标准 JSON 格式，便于 n8n 解析和后续处理。

用法:
    python daily_validator.py

退出码:
    0 - 验证通过
    1 - 验证失败
    2 - 有警告但可继续
"""

import sys
import json
import requests
from datetime import datetime
from typing import Dict, List, Tuple


def check_api(url: str = "http://localhost:5001/health", timeout: int = 5) -> bool:
    """检查 API 是否可用"""
    try:
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except:
        return False


def fetch_data(endpoint: str, base_url: str = "http://localhost:5001") -> Tuple[bool, Dict]:
    """获取数据"""
    try:
        response = requests.get(f"{base_url}{endpoint}", timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get('success', False), data
    except Exception as e:
        return False, {'error': str(e)}


def validate_daily_data() -> Dict:
    """
    执行每日数据验证

    返回结构:
    {
        "valid": bool,          # 整体是否通过
        "can_proceed": bool,    # 是否可以继续处理
        "issues": [],           # 问题列表
        "summary": {},          # 数据摘要
        "timestamp": str        # 验证时间
    }
    """
    result = {
        'valid': True,
        'can_proceed': True,
        'issues': [],
        'summary': {},
        'timestamp': datetime.now().isoformat()
    }

    # 1. 检查 API
    if not check_api():
        result['valid'] = False
        result['can_proceed'] = False
        result['issues'].append("API 服务不可用")
        return result

    # 2. 获取可转债列表
    cb_success, cb_data = fetch_data('/api/cb-list')
    if not cb_success:
        result['valid'] = False
        result['can_proceed'] = False
        result['issues'].append(f"可转债列表获取失败: {cb_data.get('error', '未知错误')}")
        return result

    cb_list = cb_data.get('cb_list', [])
    cb_count = len(cb_list)

    if cb_count == 0:
        result['valid'] = False
        result['can_proceed'] = False
        result['issues'].append("可转债列表为空")
        return result

    result['summary']['cb_count'] = cb_count

    # 检查数量阈值
    if cb_count < 300:
        result['valid'] = False
        result['can_proceed'] = False
        result['issues'].append(f"可转债数量异常: {cb_count} < 300")

    # 3. 检查正股数据
    stock_success, stock_data = fetch_data('/api/stock-data')
    if stock_success:
        spot = stock_data.get('spot', [])
        result['summary']['stock_count'] = len(spot)

        if len(spot) < cb_count * 0.9:
            result['issues'].append(f"正股数据覆盖不足: {len(spot)}/{cb_count}")
    else:
        result['issues'].append("正股数据获取失败")

    # 4. 检查股东数据
    ctrl_success, ctrl_data = fetch_data('/api/controller')
    if ctrl_success:
        ctrl = ctrl_data.get('controller_data', [])
        result['summary']['controller_count'] = len(ctrl)

        if len(ctrl) < cb_count * 0.8:
            result['issues'].append(f"股东数据覆盖不足: {len(ctrl)}/{cb_count}")
    else:
        result['issues'].append("股东数据获取失败")

    # 5. 检查财务数据
    fin_success, fin_data = fetch_data('/api/finance')
    if fin_success:
        fin = fin_data.get('finance_data', [])
        result['summary']['finance_count'] = len(fin)

        if len(fin) < cb_count * 0.7:
            result['issues'].append(f"财务数据覆盖不足: {len(fin)}/{cb_count}")
    else:
        result['issues'].append("财务数据获取失败")

    # 6. 数据一致性检查
    if cb_list:
        # 检查关键字段
        required_fields = ['转债代码', '转债名称', '正股代码', '转股价格']
        sample = cb_list[0]
        missing_fields = [f for f in required_fields if f not in sample]

        if missing_fields:
            result['valid'] = False
            result['can_proceed'] = False
            result['issues'].append(f"缺少关键字段: {', '.join(missing_fields)}")

        # 检查重复
        codes = [item.get('转债代码') for item in cb_list if item.get('转债代码')]
        if len(codes) != len(set(codes)):
            duplicates = len(codes) - len(set(codes))
            result['issues'].append(f"发现 {duplicates} 条重复数据")

    # 最终判断
    if len(result['issues']) > 0:
        # 有严重问题则标记为无效
        critical_issues = [i for i in result['issues']
                         if any(k in i for k in ['失败', '为空', '异常', '缺少关键字段'])]
        if critical_issues:
            result['valid'] = False
            result['can_proceed'] = False
        else:
            # 只有警告，可以继续
            result['can_proceed'] = True

    return result


def main():
    print("开始每日数据验证...")

    result = validate_daily_data()

    # 输出 JSON 结果（用于 n8n 解析）
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 根据结果退出
    if not result['valid']:
        sys.exit(1)
    elif result['issues']:
        sys.exit(2)  # 有警告
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
