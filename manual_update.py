#!/usr/bin/env python3
"""
手动触发数据更新 - 用于测试和立即更新
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://47.84.177.254:5001"
FRONTEND_URL = "http://47.84.177.254:3000"

def fetch_data():
    """获取所有 API 数据"""
    print("获取可转债列表...")
    cb_res = requests.get(f"{BASE_URL}/api/cb-list", timeout=120).json()

    print("获取正股行情...")
    stock_res = requests.get(f"{BASE_URL}/api/stock-data", timeout=300).json()

    print("获取股东信息...")
    ctrl_res = requests.get(f"{BASE_URL}/api/controller", timeout=120).json()

    print("获取财务数据...")
    fin_res = requests.get(f"{BASE_URL}/api/finance", timeout=120).json()

    return cb_res, stock_res, ctrl_res, fin_res

def merge_data(cb_res, stock_res, ctrl_res, fin_res):
    """合并数据"""
    cb_list = cb_res.get('cb_list', [])[:100]
    spot_list = stock_res.get('spot', [])
    ma_list = stock_res.get('ma', [])
    ctrl_list = ctrl_res.get('controller_data', [])
    fin_list = fin_res.get('finance_data', [])

    # 创建查找字典
    spot_map = {s['正股代码']: s for s in spot_list}
    ma_map = {m['正股代码']: m for m in ma_list}
    ctrl_map = {c['正股代码']: c for c in ctrl_list}
    fin_map = {f['正股代码']: f for f in fin_list}

    merged_data = []
    for cb in cb_list:
        stock_code = cb.get('正股代码', '')
        spot = spot_map.get(stock_code, {})
        ma = ma_map.get(stock_code, {})
        ctrl = ctrl_map.get(stock_code, {})
        fin = fin_map.get(stock_code, {})

        current_price = float(spot.get('当前股价', 0)) or 0
        pb = float(spot.get('PB', 1)) or 1
        net_asset = round(current_price / pb, 2) if pb else ''

        convert_price = float(cb.get('转股价格', 0)) or 0
        strong_redeem_price = round(convert_price * 1.3, 2) if convert_price else ''
        strong_redeem_pct = f"{((strong_redeem_price / current_price - 1) * 100):.1f}%" if current_price and strong_redeem_price else ''

        remain_scale = float(cb.get('可转债剩余规模', 0)) or 0
        expire_price = 115
        expire_scale = round(remain_scale * expire_price / 100, 2) if remain_scale else ''

        cash_end = fin.get('期末现金余额')
        money_fund = fin.get('货币资金')
        expire_cash_ratio = f"{(expire_scale / cash_end * 100):.0f}%" if cash_end and expire_scale else ''
        expire_money_ratio = f"{(expire_scale / money_fund * 100):.0f}%" if money_fund and expire_scale else ''

        merged_data.append({
            '正股代码': stock_code,
            '正股名称': cb.get('正股名称', ''),
            '大股东类型': ctrl.get('大股东类型', ''),
            '实际控制人': ctrl.get('实际控制人', ''),
            '实控人类型': ctrl.get('实控人类型', ''),
            '今日日期': datetime.now().strftime('%Y/%m/%d'),
            '当前股价': current_price or '',
            '每股净资产': net_asset,
            'PB': pb,
            '期末现金余额': cash_end if cash_end else '',
            '货币资金': money_fund if money_fund else '',
            '转债代码': cb.get('转债代码', ''),
            '转债名称': cb.get('转债名称', ''),
            '可转债剩余规模': remain_scale or '',
            '到期赎回价': expire_price,
            '到期赎回规模': expire_scale,
            '赎回规模占期末现金比例': expire_cash_ratio,
            '赎回规模占货币资金比例': expire_money_ratio,
            '转股价格': convert_price or '',
            '强赎价格': strong_redeem_price,
            '强赎涨幅': strong_redeem_pct,
            'MA5': ma.get('MA5', ''),
            'MA10': ma.get('MA10', ''),
            'MA20': ma.get('MA20', ''),
            '到期日期': cb.get('到期日期', ''),
            '剩余天数': '',
            '强赎状态': cb.get('强赎状态', ''),
            '最近公告内容': ''
        })

    return merged_data

def push_to_frontend(merged_data):
    """推送到前端"""
    # 生成 CSV
    if merged_data:
        headers = list(merged_data[0].keys())
        csv_rows = [','.join(headers)]
        for row in merged_data:
            csv_rows.append(','.join([str(row.get(h, '')) for h in headers]))
        csv_content = '\n'.join(csv_rows)
    else:
        csv_content = '暂无数据'

    # 推送
    payload = {
        'data': json.dumps(merged_data),
        'csv': csv_content,
        'count': len(merged_data),
        'date': datetime.now().strftime('%Y-%m-%d')
    }

    print(f"推送 {len(merged_data)} 条数据到前端...")
    res = requests.post(f"{FRONTEND_URL}/api/cb-data", data=payload, timeout=30)
    print(f"推送结果: {res.status_code}")
    print(res.json())

if __name__ == '__main__':
    print("开始手动更新数据...")
    cb_res, stock_res, ctrl_res, fin_res = fetch_data()

    print(f"获取到 {len(cb_res.get('cb_list', []))} 条可转债数据")
    print(f"获取到 {len(stock_res.get('spot', []))} 条正股行情")
    print(f"获取到 {len(ctrl_res.get('controller_data', []))} 条股东信息")
    print(f"获取到 {len(fin_res.get('finance_data', []))} 条财务数据")

    merged_data = merge_data(cb_res, stock_res, ctrl_res, fin_res)
    print(f"合并后 {len(merged_data)} 条数据")

    push_to_frontend(merged_data)
    print("更新完成!")
