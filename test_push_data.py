#!/usr/bin/env python3
"""Test script to push data to frontend API"""
import requests
import json

# Fetch data from Python API
print("Fetching data from Python API...")
cb_list = requests.get("http://localhost:5001/api/cb-list").json()
stock_data = requests.get("http://localhost:5001/api/stock-data").json()
controller_data = requests.get("http://localhost:5001/api/controller").json()
finance_data = requests.get("http://localhost:5001/api/finance").json()

print(f"CB List: {cb_list.get('count', 0)} records")
print(f"Stock Data: {len(stock_data.get('spot', []))} spot, {len(stock_data.get('ma', []))} ma")
print(f"Controller: {len(controller_data.get('controller_data', []))} records")
print(f"Finance: {len(finance_data.get('finance_data', []))} records")

# Build lookup maps
cb_items = cb_list.get('cb_list', [])
spot_map = {s['正股代码']: s for s in stock_data.get('spot', [])}
ma_map = {m['正股代码']: m for m in stock_data.get('ma', [])}
ctrl_map = {c['正股代码']: c for c in controller_data.get('controller_data', [])}
fin_map = {f['正股代码']: f for f in finance_data.get('finance_data', [])}

# Merge data
merged_data = []
for cb in cb_items[:100]:
    stock_code = cb.get('正股代码', '')
    spot = spot_map.get(stock_code, {})
    ma = ma_map.get(stock_code, {})
    ctrl = ctrl_map.get(stock_code, {})
    fin = fin_map.get(stock_code, {})

    current_price = float(spot.get('当前股价', 0) or 0)
    pb = float(spot.get('PB', 0) or 1)
    net_asset = round(current_price / pb, 2) if pb else ''
    convert_price = float(cb.get('转股价格', 0) or 0)
    strong_redeem_price = round(convert_price * 1.3, 2) if convert_price else ''
    strong_redeem_pct = f"{round((strong_redeem_price / current_price - 1) * 100, 1)}%" if current_price and strong_redeem_price else ''
    remain_scale = float(cb.get('可转债剩余规模', 0) or 0)
    expire_price = 115
    expire_scale = round(remain_scale * expire_price / 100, 2)

    cash_end = fin.get('期末现金余额') or 0
    money_fund = fin.get('货币资金') or 0
    expire_cash_ratio = f"{round(expire_scale / cash_end * 100)}%" if cash_end else ''
    expire_money_ratio = f"{round(expire_scale / money_fund * 100)}%" if money_fund else ''

    # Calculate days to expiry
    expire_date = cb.get('到期日期', '')
    days_left = ''
    if expire_date:
        try:
            from datetime import datetime
            exp = datetime.strptime(expire_date, '%a, %d %b %Y %H:%M:%S GMT')
            days_left = (exp - datetime.now()).days
        except:
            pass

    merged_data.append({
        '正股代码': stock_code,
        '正股名称': cb.get('正股名称', ''),
        '大股东类型': ctrl.get('大股东类型', ''),
        '实际控制人': ctrl.get('实际控制人', ''),
        '实控人类型': ctrl.get('实控人类型', ''),
        '今日日期': '2026/03/29',
        '当前股价': current_price or '',
        '每股净资产': net_asset,
        'PB': pb,
        '期末现金余额': cash_end or '',
        '货币资金': money_fund or '',
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
        '到期日期': expire_date,
        '剩余天数': days_left,
        '最近公告内容': ''
    })

print(f"\nMerged {len(merged_data)} records")

# Generate CSV
headers = list(merged_data[0].keys()) if merged_data else []
csv_rows = [','.join(headers)]
for row in merged_data:
    csv_rows.append(','.join([f'"{str(row.get(h, ""))}"' if ',' in str(row.get(h, '')) else str(row.get(h, '')) for h in headers]))
csv_content = '\n'.join(csv_rows)

# Push to frontend
print("\nPushing to frontend API...")
response = requests.post(
    "http://localhost:3000/api/cb-data",
    data={
        'data': json.dumps(merged_data),
        'csv': csv_content,
        'count': len(merged_data),
        'date': '2026-03-29'
    }
)
print(f"Response: {response.status_code}")
print(f"Body: {response.json()}")
