#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取正股行情与均线数据
使用 AkShare 的 stock_zh_a_spot_em() 和 stock_zh_a_hist() 接口
"""
import akshare as ak
import pandas as pd
import json
import sys

def main():
    try:
        # 获取全部A股实时行情
        spot = ak.stock_zh_a_spot_em()
        spot = spot[['代码', '最新价', '每股净资产']]
        spot.columns = ['正股代码', '当前股价', '每股净资产']

        # 计算均线（采样前50只避免超时）
        ma_data = []
        sample_codes = spot['正股代码'].head(50).tolist()

        for code in sample_codes:
            try:
                hist = ak.stock_zh_a_hist(
                    symbol=code,
                    period='daily',
                    start_date='20250101',
                    adjust='qfq'
                )
                if len(hist) >= 20:
                    ma5 = round(hist['收盘'].tail(5).mean(), 2)
                    ma10 = round(hist['收盘'].tail(10).mean(), 2)
                    ma20 = round(hist['收盘'].tail(20).mean(), 2)
                    ma_data.append({
                        '正股代码': code,
                        'MA5': ma5,
                        'MA10': ma10,
                        'MA20': ma20
                    })
            except:
                pass

        result = {
            'spot': spot.to_dict(orient='records'),
            'ma': ma_data,
            'success': True
        }
        print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        result = {
            'spot': [],
            'ma': [],
            'success': False,
            'error': str(e)
        }
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)

if __name__ == '__main__':
    main()
