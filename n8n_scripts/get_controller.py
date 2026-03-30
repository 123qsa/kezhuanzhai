#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取股东与实控人信息
使用 AkShare 的 stock_individual_info_em() 接口
"""
import akshare as ak
import json
import sys

def get_controller_info(code):
    """获取单个股票的实控人信息"""
    try:
        info = ak.stock_individual_info_em(symbol=code)
        info_dict = dict(zip(info['item'], info['value']))
        return {
            '正股代码': code,
            '实际控制人': info_dict.get('实际控制人', ''),
            '大股东类型': '自然人股' if '个人' in str(info_dict.get('实际控制人性质', '')) else '法人股',
            '实控人类型': info_dict.get('实际控制人性质', '')
        }
    except:
        return {'正股代码': code}

def main():
    try:
        # 获取样本数据（前30只）
        spot = ak.stock_zh_a_spot_em()
        sample_codes = spot['代码'].head(30).tolist()
        results = [get_controller_info(c) for c in sample_codes]

        output = {
            'controller_data': results,
            'success': True
        }
        print(json.dumps(output, ensure_ascii=False))
    except Exception as e:
        output = {
            'controller_data': [],
            'success': False,
            'error': str(e)
        }
        print(json.dumps(output, ensure_ascii=False))
        sys.exit(1)

if __name__ == '__main__':
    main()
