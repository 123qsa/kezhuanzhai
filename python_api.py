#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python API 服务 - 为 n8n 提供 AkShare 数据接口
"""
from flask import Flask, jsonify
import akshare as ak
import json
import sys
from datetime import datetime, date

app = Flask(__name__)

class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.strftime('%Y-%m-%d')
        return super().default(obj)

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/api/check-trade-day')
def check_trade_day():
    """检查是否为交易日"""
    try:
        import datetime as dt
        today = dt.date.today().strftime('%Y%m%d')
        trade_dates = ak.tool_trade_date_hist_sina()
        trade_list = trade_dates['trade_date'].astype(str).tolist()
        is_trade_day = today in trade_list
        return jsonify({
            'is_trade_day': is_trade_day,
            'today': today,
            'success': True
        })
    except Exception as e:
        return jsonify({
            'is_trade_day': True,
            'error': str(e),
            'success': False
        })

@app.route('/api/cb-list')
def get_cb_list():
    """获取可转债列表 - 使用集思录强赎数据(355条)"""
    try:
        # 使用 bond_cb_redeem_jsl 获取更多数据(约355条)
        df = ak.bond_cb_redeem_jsl()

        # 转换日期列为字符串
        date_cols = ['转股起始日', '最后交易日', '到期日']
        for col in date_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).replace('nan', '')

        # 处理数值列的NaN
        numeric_cols = ['规模', '剩余规模', '现价', '转股价', '正股价', '强赎触发价', '强赎价']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = df[col].fillna(0)

        # 重命名字段以匹配工作流
        column_mapping = {
            '代码': '转债代码',
            '名称': '转债名称',
            '正股代码': '正股代码',
            '正股名称': '正股名称',
            '转股价': '转股价格',
            '剩余规模': '可转债剩余规模',
            '到期日': '到期日期',
            '正股价': '当前股价',
            '强赎触发比': '强赎触发比例',
            '强赎触发价': '强赎触发价格',
            '强赎价': '强赎价格',
            '强赎状态': '强赎状态',
            '规模': '发行规模'
        }

        # 只重命名存在的列
        existing_mapping = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df.rename(columns=existing_mapping)

        result = df.to_dict(orient='records')
        return jsonify({
            'cb_list': result,
            'count': len(result),
            'success': True
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'cb_list': [],
            'count': 0,
            'success': False,
            'error': str(e)
        })

@app.route('/api/stock-data')
def get_stock_data():
    """获取正股行情与均线"""
    try:
        spot = ak.stock_zh_a_spot_em()
        # 使用市净率(PB)列
        spot = spot[['代码', '名称', '最新价', '市净率']].copy()
        spot.columns = ['正股代码', '正股名称', '当前股价', 'PB']

        # 获取可转债列表中的正股代码用于MA计算（限制数量避免超时）
        try:
            cb_df = ak.bond_cb_redeem_jsl()
            cb_stock_codes = cb_df['正股代码'].unique().tolist()[:100]  # 前100只
        except:
            cb_stock_codes = spot['正股代码'].head(100).tolist()

        # 计算均线
        ma_data = []
        for code in cb_stock_codes:
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

        # 转换 spot 为可序列化格式
        spot_list = spot.to_dict(orient='records')

        return jsonify({
            'spot': spot_list,
            'ma': ma_data,
            'success': True
        })
    except Exception as e:
        return jsonify({
            'spot': [],
            'ma': [],
            'success': False,
            'error': str(e)
        })

@app.route('/api/controller')
def get_controller():
    """获取股东与实控人信息"""
    try:
        # 使用与 cb-list 相同的数据源
        try:
            cb_df = ak.bond_cb_redeem_jsl()
            stock_codes = cb_df['正股代码'].unique().tolist()
        except:
            stock_codes = []

        def get_controller_info(code):
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
                return {'正股代码': code, '实际控制人': '', '大股东类型': '', '实控人类型': ''}

        results = [get_controller_info(c) for c in stock_codes]

        return jsonify({
            'controller_data': results,
            'success': True
        })
    except Exception as e:
        return jsonify({
            'controller_data': [],
            'success': False,
            'error': str(e)
        })

@app.route('/api/finance')
def get_finance():
    """获取财务数据"""
    try:
        # 使用与 cb-list 相同的数据源
        try:
            cb_df = ak.bond_cb_redeem_jsl()
            stock_codes = cb_df['正股代码'].unique().tolist()
        except:
            stock_codes = []

        def get_finance_data(code):
            try:
                cf = ak.stock_financial_cash_flow_em(symbol=code)
                cash_end = cf.iloc[0].get('期末现金及现金等价物余额', None) if len(cf) > 0 else None
                bs = ak.stock_financial_balance_sheet_em(symbol=code)
                money_fund = bs.iloc[0].get('货币资金', None) if len(bs) > 0 else None
                return {
                    '正股代码': code,
                    '期末现金余额': cash_end,
                    '货币资金': money_fund
                }
            except:
                return {'正股代码': code, '期末现金余额': None, '货币资金': None}

        results = [get_finance_data(c) for c in stock_codes]

        return jsonify({
            'finance_data': results,
            'success': True
        })
    except Exception as e:
        return jsonify({
            'finance_data': [],
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    print("Python API 服务启动中...")
    print("访问 http://localhost:5001 查看 API")
    app.run(host='0.0.0.0', port=5001, debug=False)
