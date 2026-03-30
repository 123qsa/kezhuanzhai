#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取财务数据
使用 AkShare 的 stock_financial_cash_flow_em() 和 stock_financial_balance_sheet_em() 接口
"""
import akshare as ak
import json
import sys

def get_finance(code):
    """获取单个股票的财务数据"""
    try:
        # 现金流量表
        cf = ak.stock_financial_cash_flow_em(symbol=code)
        cash_end = cf.iloc[0].get('期末现金及现金等价物余额', None) if len(cf) > 0 else None

        # 资产负债表
        bs = ak.stock_financial_balance_sheet_em(symbol=code)
        money_fund = bs.iloc[0].get('货币资金', None) if len(bs) > 0 else None

        return {
            '正股代码': code,
            '期末现金余额': cash_end,
            '货币资金': money_fund
        }
    except:
        return {'正股代码': code}

def main():
    try:
        # 获取样本数据（前30只）
        spot = ak.stock_zh_a_spot_em()
        sample_codes = spot['代码'].head(30).tolist()
        results = [get_finance(c) for c in sample_codes]

        output = {
            'finance_data': results,
            'success': True
        }
        print(json.dumps(output, ensure_ascii=False))
    except Exception as e:
        output = {
            'finance_data': [],
            'success': False,
            'error': str(e)
        }
        print(json.dumps(output, ensure_ascii=False))
        sys.exit(1)

if __name__ == '__main__':
    main()
