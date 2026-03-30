#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取A股可转债列表
使用 AkShare 的 bond_cb_jsl() 接口
"""
import akshare as ak
import json
import sys
from datetime import datetime, date

class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.strftime('%Y-%m-%d')
        return super().default(obj)

def main():
    try:
        df = ak.bond_cb_jsl()
        # 转换日期列为字符串
        for col in df.columns:
            if df[col].dtype == 'datetime64[ns]':
                df[col] = df[col].dt.strftime('%Y-%m-%d')
        result = df.to_dict(orient='records')
        output = {
            'cb_list': result,
            'count': len(result),
            'success': True
        }
        print(json.dumps(output, ensure_ascii=False, cls=DateEncoder))
    except Exception as e:
        output = {
            'cb_list': [],
            'count': 0,
            'success': False,
            'error': str(e)
        }
        print(json.dumps(output, ensure_ascii=False))
        sys.exit(1)

if __name__ == '__main__':
    main()
