#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：模拟可转债数据推送
用于验证前端 API 是否正常工作
"""
import requests
import json
from datetime import datetime

# 模拟可转债数据
test_data = [
    {
        "正股代码": "000001",
        "正股名称": "平安银行",
        "大股东类型": "法人股",
        "实际控制人": "中国平安",
        "实控人类型": "境内非国有法人",
        "今日日期": datetime.now().strftime("%Y/%m/%d"),
        "当前股价": 10.50,
        "每股净资产": 12.30,
        "PB": 0.85,
        "期末现金余额": 1500000000,
        "货币资金": 1200000000,
        "转债代码": "000001.SZ",
        "转债名称": "平安转债",
        "可转债剩余规模": 50.5,
        "到期赎回价": 115,
        "到期赎回规模": 58.08,
        "赎回规模占期末现金比例": "4%",
        "赎回规模占货币资金比例": "5%",
        "转股价格": 13.20,
        "强赎价格": 17.16,
        "强赎涨幅": "63.4%",
        "MA5": 10.45,
        "MA10": 10.38,
        "MA20": 10.25,
        "到期日期": "2027-12-31",
        "剩余天数": 1003,
        "最近公告内容": ""
    },
    {
        "正股代码": "600519",
        "正股名称": "贵州茅台",
        "大股东类型": "自然人股",
        "实际控制人": "贵州省国资委",
        "实控人类型": "地方国资委",
        "今日日期": datetime.now().strftime("%Y/%m/%d"),
        "当前股价": 1680.00,
        "每股净资产": 159.20,
        "PB": 10.55,
        "期末现金余额": 5000000000,
        "货币资金": 4500000000,
        "转债代码": "600519.SH",
        "转债名称": "茅台转债",
        "可转债剩余规模": 25.0,
        "到期赎回价": 115,
        "到期赎回规模": 28.75,
        "赎回规模占期末现金比例": "1%",
        "赎回规模占货币资金比例": "1%",
        "转股价格": 1800.00,
        "强赎价格": 2340.00,
        "强赎涨幅": "39.3%",
        "MA5": 1675.50,
        "MA10": 1668.20,
        "MA20": 1650.80,
        "到期日期": "2026-06-15",
        "剩余天数": 809,
        "最近公告内容": ""
    },
    {
        "正股代码": "300750",
        "正股名称": "宁德时代",
        "大股东类型": "自然人股",
        "实际控制人": "曾毓群",
        "实控人类型": "自然人",
        "今日日期": datetime.now().strftime("%Y/%m/%d"),
        "当前股价": 185.50,
        "每股净资产": 45.80,
        "PB": 4.05,
        "期末现金余额": 800000000,
        "货币资金": 720000000,
        "转债代码": "300750.SZ",
        "转债名称": "宁德转债",
        "可转债剩余规模": 35.0,
        "到期赎回价": 115,
        "到期赎回规模": 40.25,
        "赎回规模占期末现金比例": "5%",
        "赎回规模占货币资金比例": "6%",
        "转股价格": 210.00,
        "强赎价格": 273.00,
        "强赎涨幅": "47.2%",
        "MA5": 183.20,
        "MA10": 180.50,
        "MA20": 178.30,
        "到期日期": "2026-09-20",
        "剩余天数": 906,
        "最近公告内容": ""
    },
    {
        "正股代码": "000858",
        "正股名称": "五粮液",
        "大股东类型": "法人股",
        "实际控制人": "宜宾市国资委",
        "实控人类型": "地方国资委",
        "今日日期": datetime.now().strftime("%Y/%m/%d"),
        "当前股价": 145.80,
        "每股净资产": 32.50,
        "PB": 4.49,
        "期末现金余额": 1200000000,
        "货币资金": 1100000000,
        "转债代码": "000858.SZ",
        "转债名称": "五粮转债",
        "可转债剩余规模": 40.0,
        "到期赎回价": 115,
        "到期赎回规模": 46.00,
        "赎回规模占期末现金比例": "4%",
        "赎回规模占货币资金比例": "4%",
        "转股价格": 160.00,
        "强赎价格": 208.00,
        "强赎涨幅": "42.7%",
        "MA5": 144.20,
        "MA10": 143.50,
        "MA20": 142.80,
        "到期日期": "2026-12-25",
        "剩余天数": 1002,
        "最近公告内容": ""
    },
    {
        "正股代码": "002594",
        "正股名称": "比亚迪",
        "大股东类型": "自然人股",
        "实际控制人": "王传福",
        "实控人类型": "自然人",
        "今日日期": datetime.now().strftime("%Y/%m/%d"),
        "当前股价": 245.60,
        "每股净资产": 38.90,
        "PB": 6.31,
        "期末现金余额": 2500000000,
        "货币资金": 2300000000,
        "转债代码": "002594.SZ",
        "转债名称": "比亚转债",
        "可转债剩余规模": 60.0,
        "到期赎回价": 115,
        "到期赎回规模": 69.00,
        "赎回规模占期末现金比例": "3%",
        "赎回规模占货币资金比例": "3%",
        "转股价格": 280.00,
        "强赎价格": 364.00,
        "强赎涨幅": "48.2%",
        "MA5": 242.80,
        "MA10": 240.50,
        "MA20": 238.20,
        "到期日期": "2026-03-15",
        "剩余天数": 717,
        "最近公告内容": ""
    }
]

# 生成 CSV
def generate_csv(data):
    if not data:
        return ""
    headers = list(data[0].keys())
    rows = [",".join(headers)]
    for item in data:
        row = []
        for h in headers:
            val = item.get(h, "")
            if isinstance(val, str) and "," in val:
                val = f'"{val}"'
            row.append(str(val))
        rows.append(",".join(row))
    return "\n".join(rows)

def test_push():
    """测试数据推送"""
    url = "http://localhost:3000/api/cb-data"

    payload = {
        "data": json.dumps(test_data),
        "csv": generate_csv(test_data),
        "count": len(test_data),
        "date": datetime.now().isoformat()
    }

    print(f"正在推送 {len(test_data)} 条测试数据...")
    print(f"API 地址: {url}")

    try:
        response = requests.post(url, data=payload, timeout=10)
        print(f"\n状态码: {response.status_code}")
        print(f"响应: {response.json()}")

        if response.status_code == 200:
            print("\n✅ 数据推送成功！")
            print("\n现在可以访问 http://localhost:3000 查看前端展示")
            return True
    except requests.exceptions.ConnectionError:
        print("\n❌ 连接失败！请检查前端 API 服务是否已启动")
        print("运行命令: cd frontend-api && npm start")
    except Exception as e:
        print(f"\n❌ 错误: {e}")

    return False

def test_get():
    """测试数据获取"""
    url = "http://localhost:3000/api/cb-data"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        print(f"\n获取数据成功:")
        print(f"- 总数: {data.get('count', 0)}")
        print(f"- 日期: {data.get('date', 'N/A')}")
        print(f"- 数据条数: {len(data.get('data', []))}")
    except Exception as e:
        print(f"获取数据失败: {e}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "get":
        test_get()
    else:
        if test_push():
            print("\n" + "="*50)
            print("5秒后自动验证数据是否写入...")
            import time
            time.sleep(5)
            test_get()
