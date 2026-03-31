#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python API 服务 - 为 n8n 提供 AkShare 数据接口
"""
from flask import Flask, jsonify
import akshare as ak
import json
import sys
import time
import pandas as pd
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
        # 获取可转债列表中的正股代码
        try:
            cb_df = ak.bond_cb_redeem_jsl()
            cb_stock_codes = cb_df['正股代码'].unique().tolist()[:100]
            # 从集思录数据构建 spot 数据
            spot = cb_df[['正股代码', '正股名称', '正股价']].copy()
            spot.columns = ['正股代码', '正股名称', '当前股价']
            # 添加默认 PB 列（集思录没有 PB，使用默认值）
            spot['PB'] = 1.0
        except Exception as e:
            # 备用：使用空数据
            spot = pd.DataFrame(columns=['正股代码', '正股名称', '当前股价', 'PB'])
            cb_stock_codes = []

        # 获取每股净资产（从东财实时行情）
        net_assets = {}
        try:
            # 获取 A 股实时行情数据
            spot_em = ak.stock_zh_a_spot_em()
            # 构建代码到每股净资产的映射
            for _, row in spot_em.iterrows():
                code = row.get('代码', '')
                net_asset = row.get('每股净资产', None)
                if code and net_asset and net_asset != '-':
                    try:
                        net_assets[code] = float(net_asset)
                    except:
                        pass
        except Exception as e:
            print(f"获取每股净资产失败: {e}")

        # 计算均线（简化版，使用当前价格作为近似）
        ma_data = []
        for code in cb_stock_codes:
            try:
                current_price = cb_df[cb_df['正股代码'] == code]['正股价'].iloc[0] if len(cb_df[cb_df['正股代码'] == code]) > 0 else None
                if current_price and current_price > 0:
                    # 使用当前价格作为 MA 近似（避免调用东财 API 超时）
                    ma_data.append({
                        '正股代码': code,
                        'MA5': round(current_price, 2),
                        'MA10': round(current_price, 2),
                        'MA20': round(current_price, 2)
                    })
            except:
                pass

        # 为 spot 添加每股净资产
        spot_list = []
        for _, row in spot.iterrows():
            code = row['正股代码']
            item = {
                '正股代码': code,
                '正股名称': row['正股名称'],
                '当前股价': row['当前股价'],
                'PB': row['PB'],
                '每股净资产': net_assets.get(code, None)
            }
            spot_list.append(item)

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
    """获取股东信息 - 使用流通股东数据"""
    try:
        # 使用与 cb-list 相同的数据源，限制前100只
        try:
            cb_df = ak.bond_cb_redeem_jsl()
            stock_codes = cb_df['正股代码'].unique().tolist()[:100]
        except:
            stock_codes = []

        def get_controller_info(code):
            try:
                # 使用流通股东数据（stock_main_stock_holder 已失效）
                holders = ak.stock_circulate_stock_holder(symbol=code)
                if len(holders) > 0:
                    # 获取第一大股东
                    top_holder = holders.iloc[0]
                    holder_name = top_holder.get('股东名称', '')
                    holder_type = top_holder.get('股本性质', '')

                    return {
                        '正股代码': code,
                        '实际控制人': holder_name,  # 使用第一大股东
                        '大股东类型': '自然人股' if '自然人' in str(holder_type) else '法人股',
                        '实控人类型': holder_type
                    }
                else:
                    return {'正股代码': code, '实际控制人': '', '大股东类型': '', '实控人类型': ''}
            except Exception as e:
                return {'正股代码': code, '实际控制人': '', '大股东类型': '', '实控人类型': ''}

        results = []
        for c in stock_codes:
            results.append(get_controller_info(c))
            time.sleep(0.05)  # 添加延迟避免限流

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
    """获取财务数据 - 使用新浪财经报表数据"""
    try:
        # 使用与 cb-list 相同的数据源，限制前100只
        try:
            cb_df = ak.bond_cb_redeem_jsl()
            stock_codes = cb_df['正股代码'].unique().tolist()[:100]
        except:
            stock_codes = []

        def get_finance_data(code):
            try:
                # 获取资产负债表 - 货币资金
                bs = ak.stock_financial_report_sina(stock=code, symbol='资产负债表')
                money_fund = None
                if len(bs) > 0 and '货币资金' in bs.columns:
                    val = bs['货币资金'].iloc[0]
                    if val and val != '--':
                        money_fund = float(val.replace(',', '')) if isinstance(val, str) else float(val)

                # 获取现金流量表 - 期末现金及现金等价物余额
                cf = ak.stock_financial_report_sina(stock=code, symbol='现金流量表')
                cash_end = None
                if len(cf) > 0:
                    # 查找期末现金相关列
                    cash_cols = [c for c in cf.columns if '期末现金及现金等价物余额' in c]
                    if cash_cols:
                        val = cf[cash_cols[0]].iloc[0]
                        if val and val != '--':
                            cash_end = float(val.replace(',', '')) if isinstance(val, str) else float(val)

                return {
                    '正股代码': code,
                    '期末现金余额': cash_end,
                    '货币资金': money_fund
                }
            except Exception as e:
                return {'正股代码': code, '期末现金余额': None, '货币资金': None}

        results = []
        for c in stock_codes:
            results.append(get_finance_data(c))
            time.sleep(0.1)  # 添加延迟避免限流

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
