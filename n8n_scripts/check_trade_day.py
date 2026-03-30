#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
判断今天是否为交易日
使用 AkShare 的 tool_trade_date_hist_sina() 接口
"""
import akshare as ak
import datetime
import json
import sys

def main():
    try:
        today = datetime.date.today().strftime('%Y%m%d')
        trade_dates = ak.tool_trade_date_hist_sina()
        trade_list = trade_dates['trade_date'].astype(str).tolist()
        is_trade_day = today in trade_list
        result = {
            'is_trade_day': is_trade_day,
            'today': today,
            'success': True
        }
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        result = {
            'is_trade_day': True,  # 默认继续执行
            'error': str(e),
            'success': False
        }
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)

if __name__ == '__main__':
    main()
