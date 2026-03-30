#!/usr/bin/env python3
"""Test script to push full CB data to frontend"""
import requests
import json
import math

# Custom JSON encoder to handle NaN/Infinity
def clean_for_json(obj):
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: clean_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_for_json(v) for v in obj]
    return obj

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

print("\nMerging data...")
merged_data = []
for cb in cb_items:
    stock_code = cb.get('正股代码', '')
    spot = spot_map.get(stock_code, {})
    ma = ma_map.get(stock_code, {})
    ctrl = ctrl_map.get(stock_code, {})
    fin = fin_map.get(stock_code, {})

    # Handle NaN in numeric fields
    def safe_float(val, default=0):
        try:
            f = float(val or default)
            if math.isnan(f) or math.isinf(f):
                return default
            return f
        except:
            return default

    current_price = safe_float(spot.get('当前股价') or cb.get('当前股价'))
    pb = safe_float(spot.get('PB'), 1)
    net_asset = round(current_price / pb, 2) if pb and current_price else ''
    convert_price = safe_float(cb.get('转股价格'))
    strong_redeem_price = round(convert_price * 1.3, 2) if convert_price else ''
    strong_redeem_pct = f"{round((strong_redeem_price / current_price - 1) * 100, 1)}%" if current_price and strong_redeem_price else ''
    remain_scale = safe_float(cb.get('可转债剩余规模'))
    expire_price = 115
    expire_scale = round(remain_scale * expire_price / 100, 2)

    cash_end = fin.get('期末现金余额') or ''
    money_fund = fin.get('货币资金') or ''
    expire_cash_ratio = f"{round(expire_scale / cash_end * 100)}%" if cash_end and isinstance(cash_end, (int, float)) else ''
    expire_money_ratio = f"{round(expire_scale / money_fund * 100)}%" if money_fund and isinstance(money_fund, (int, float)) else ''

    # Calculate days to expiry
    expire_date = cb.get('到期日期', '')
    days_left = ''
    if expire_date and expire_date != 'nan' and expire_date != 'None':
        try:
            from datetime import datetime
            exp = datetime.strptime(expire_date, '%Y-%m-%d')
            days_left = (exp - datetime.now()).days
        except:
            pass

    # Clean all values
    def clean_val(v):
        if v is None or v == 'None' or v == 'nan' or v == 'NaN':
            return ''
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return ''
        return v

    merged_data.append({
        '正股代码': clean_val(stock_code),
        '正股名称': clean_val(cb.get('正股名称')),
        '大股东类型': clean_val(ctrl.get('大股东类型')),
        '实际控制人': clean_val(ctrl.get('实际控制人')),
        '实控人类型': clean_val(ctrl.get('实控人类型')),
        '今日日期': '2026/03/29',
        '当前股价': clean_val(current_price) if current_price else '',
        '每股净资产': clean_val(net_asset),
        'PB': clean_val(pb) if pb != 1 else '',
        '期末现金余额': clean_val(cash_end),
        '货币资金': clean_val(money_fund),
        '转债代码': clean_val(cb.get('转债代码')),
        '转债名称': clean_val(cb.get('转债名称')),
        '可转债剩余规模': clean_val(remain_scale) if remain_scale else '',
        '到期赎回价': expire_price,
        '到期赎回规模': expire_scale,
        '赎回规模占期末现金比例': expire_cash_ratio,
        '赎回规模占货币资金比例': expire_money_ratio,
        '转股价格': clean_val(convert_price) if convert_price else '',
        '强赎价格': strong_redeem_price,
        '强赎涨幅': strong_redeem_pct,
        'MA5': clean_val(ma.get('MA5')),
        'MA10': clean_val(ma.get('MA10')),
        'MA20': clean_val(ma.get('MA20')),
        '到期日期': clean_val(expire_date),
        '剩余天数': days_left,
        '强赎状态': clean_val(cb.get('强赎状态')),
        '最近公告内容': ''
    })

print(f"\nMerged {len(merged_data)} records")

# Clean data
cleaned_data = clean_for_json(merged_data)

# Generate CSV
headers = list(cleaned_data[0].keys()) if cleaned_data else []
csv_rows = [','.join(headers)]
for row in cleaned_data:
    row_values = []
    for h in headers:
        val = str(row.get(h, "")).replace(chr(10), " ").replace(chr(13), " ")
        row_values.append(f'"{val}"')
    csv_rows.append(','.join(row_values))
csv_content = '\n'.join(csv_rows)

# Prepare data
data_json = json.dumps(cleaned_data, ensure_ascii=False, default=str)

print(f"JSON size: {len(data_json)} bytes")
print(f"CSV size: {len(csv_content)} bytes")

# Verify JSON is valid
try:
    json.loads(data_json)
    print("JSON validation: PASSED")
except Exception as e:
    print(f"JSON validation FAILED: {e}")

# Push to frontend
print("\nPushing to frontend API...")
response = requests.post(
    "http://47.84.177.254:3000/api/cb-data",
    data={
        'data': data_json,
        'csv': csv_content,
        'count': str(len(cleaned_data)),
        'date': '2026-03-29'
    }
)
print(f"Response: {response.status_code}")
print(f"Body: {response.text}")
