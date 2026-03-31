#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可转债数据采集器

采集所有必要数据并生成标准格式的 CSV 文件。
"""

import requests
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import os


class CBCollector:
    """可转债数据采集器"""

    def __init__(self, base_url: str = "http://localhost:5001"):
        self.base_url = base_url
        self.data = {
            'cb_list': [],
            'stock_spot': [],
            'stock_ma': [],
            'controller': [],
            'finance': []
        }

    def _fetch(self, endpoint: str) -> Tuple[bool, Dict]:
        """获取 API 数据"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data.get('success', False), data
        except Exception as e:
            print(f"获取 {endpoint} 失败: {e}")
            return False, {'error': str(e)}

    def collect_all(self) -> bool:
        """采集所有数据"""
        print("开始采集数据...")

        # 1. 可转债列表
        print("[1/4] 采集可转债列表...")
        success, data = self._fetch('/api/cb-list')
        if success:
            self.data['cb_list'] = data.get('cb_list', [])
            print(f"  获取 {len(self.data['cb_list'])} 条可转债数据")
        else:
            print(f"  失败: {data.get('error')}")
            return False

        # 2. 正股数据
        print("[2/4] 采集正股数据...")
        success, data = self._fetch('/api/stock-data')
        if success:
            self.data['stock_spot'] = data.get('spot', [])
            self.data['stock_ma'] = data.get('ma', [])
            print(f"  获取 {len(self.data['stock_spot'])} 条正股数据")
        else:
            print(f"  失败: {data.get('error')}")

        # 3. 股东数据
        print("[3/4] 采集股东数据...")
        success, data = self._fetch('/api/controller')
        if success:
            self.data['controller'] = data.get('controller_data', [])
            print(f"  获取 {len(self.data['controller'])} 条股东数据")
        else:
            print(f"  失败: {data.get('error')}")

        # 4. 财务数据
        print("[4/4] 采集财务数据...")
        success, data = self._fetch('/api/finance')
        if success:
            self.data['finance'] = data.get('finance_data', [])
            print(f"  获取 {len(self.data['finance'])} 条财务数据")
        else:
            print(f"  失败: {data.get('error')}")

        return len(self.data['cb_list']) > 0

    def _safe_float(self, value, default: float = 0.0) -> float:
        """安全转换为浮点数"""
        if value is None or value == '' or value == '-':
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def _safe_get(self, data_list: List[Dict], key_field: str, key_value: str, value_field: str, default=None):
        """从列表中安全获取字段值"""
        for item in data_list:
            if item.get(key_field) == key_value:
                return item.get(value_field, default)
        return default

    def merge_and_calculate(self) -> pd.DataFrame:
        """合并数据并计算派生字段"""
        print("\n合并数据并计算派生字段...")

        # 构建查找映射
        spot_map = {item['正股代码']: item for item in self.data['stock_spot'] if item.get('正股代码')}
        ma_map = {item['正股代码']: item for item in self.data['stock_ma'] if item.get('正股代码')}
        ctrl_map = {item['正股代码']: item for item in self.data['controller'] if item.get('正股代码')}
        fin_map = {item['正股代码']: item for item in self.data['finance'] if item.get('正股代码')}

        today = datetime.now()
        today_str = today.strftime('%Y-%m-%d')

        results = []

        for cb in self.data['cb_list']:
            stock_code = cb.get('正股代码', '')

            # 基础数据
            spot = spot_map.get(stock_code, {})
            ma = ma_map.get(stock_code, {})
            ctrl = ctrl_map.get(stock_code, {})
            fin = fin_map.get(stock_code, {})

            # 数值字段转换
            current_price = self._safe_float(spot.get('当前股价') or cb.get('当前股价'))
            net_asset = self._safe_float(spot.get('每股净资产'))
            convert_price = self._safe_float(cb.get('转股价格'))
            remain_scale = self._safe_float(cb.get('可转债剩余规模'))
            cash_end = self._safe_float(fin.get('期末现金余额'))
            money_fund = self._safe_float(fin.get('货币资金'))

            # 计算派生字段
            # PB = 当前股价 / 每股净资产
            pb = round(current_price / net_asset, 2) if net_asset > 0 else None

            # 到期赎回价（固定值）
            expire_price = 115.0

            # 到期赎回规模 = 剩余规模 * 115 / 100
            expire_scale = round(remain_scale * expire_price / 100, 2) if remain_scale > 0 else 0

            # 赎回规模占期末现金比
            expire_cash_ratio = round(expire_scale / cash_end * 100, 0) if cash_end > 0 else None

            # 赎回规模占货币资金比
            expire_money_ratio = round(expire_scale / money_fund * 100, 0) if money_fund > 0 else None

            # 强赎价格 = 转股价格 * 1.3
            strong_redeem_price = round(convert_price * 1.3, 2) if convert_price > 0 else None

            # 强赎涨幅 = (强赎价格/当前股价 - 1) * 100%
            strong_redeem_pct = None
            if strong_redeem_price and current_price > 0:
                strong_redeem_pct = round((strong_redeem_price / current_price - 1) * 100, 1)

            # 剩余天数
            expire_date_str = cb.get('到期日期', '')
            remain_days = None
            if expire_date_str and expire_date_str != 'nan':
                try:
                    expire_date = datetime.strptime(str(expire_date_str)[:10], '%Y-%m-%d')
                    remain_days = (expire_date - today).days
                except:
                    pass

            # 构建结果行
            row = {
                '正股代码': stock_code,
                '正股名称': cb.get('正股名称', ''),
                '大股东类型': ctrl.get('大股东类型', ''),
                '实际控制人': ctrl.get('实际控制人', ''),
                '实控人类型': ctrl.get('实控人类型', ''),
                '今日日期': today_str,
                '当前股价': current_price if current_price > 0 else None,
                '每股净资产': net_asset if net_asset > 0 else None,
                'PB': pb,
                '期末现金余额': cash_end if cash_end > 0 else None,
                '货币资金': money_fund if money_fund > 0 else None,
                '转债代码': cb.get('转债代码', ''),
                '转债名称': cb.get('转债名称', ''),
                '转债剩余规模': remain_scale if remain_scale > 0 else None,
                '到期赎回价': expire_price,
                '到期赎回规模': expire_scale if expire_scale > 0 else None,
                '赎回规模占期末现金比': f"{int(expire_cash_ratio)}%" if expire_cash_ratio is not None else '',
                '赎回规模占货币资金比': f"{int(expire_money_ratio)}%" if expire_money_ratio is not None else '',
                '转股价格': convert_price if convert_price > 0 else None,
                '强赎价格': strong_redeem_price,
                '强赎涨幅': f"{strong_redeem_pct}%" if strong_redeem_pct is not None else '',
                'MA5': ma.get('MA5'),
                'MA10': ma.get('MA10'),
                'MA20': ma.get('MA20'),
                '到期日期': expire_date_str if expire_date_str != 'nan' else '',
                '剩余天数': remain_days
            }

            results.append(row)

        df = pd.DataFrame(results)
        print(f"合并完成: {len(df)} 行数据")
        return df

    def save_to_csv(self, df: pd.DataFrame, output_dir: str = "output") -> str:
        """保存为 CSV 文件"""
        os.makedirs(output_dir, exist_ok=True)

        today_str = datetime.now().strftime('%Y%m%d')
        filename = f"cb_data_{today_str}.csv"
        filepath = os.path.join(output_dir, filename)

        # 定义列顺序（按图片中的顺序）
        columns = [
            '正股代码', '正股名称', '大股东类型', '实际控制人', '实控人类型',
            '今日日期', '当前股价', '每股净资产', 'PB',
            '期末现金余额', '货币资金',
            '转债代码', '转债名称', '转债剩余规模', '到期赎回价', '到期赎回规模',
            '赎回规模占期末现金比', '赎回规模占货币资金比',
            '转股价格', '强赎价格', '强赎涨幅',
            'MA5', 'MA10', 'MA20',
            '到期日期', '剩余天数'
        ]

        # 确保所有列都存在
        for col in columns:
            if col not in df.columns:
                df[col] = ''

        df.to_csv(filepath, index=False, encoding='utf-8-sig', columns=columns)
        print(f"CSV 文件已保存: {filepath}")
        return filepath


def main():
    """测试采集功能"""
    collector = CBCollector()

    if collector.collect_all():
        df = collector.merge_and_calculate()
        collector.save_to_csv(df)
    else:
        print("数据采集失败")


if __name__ == '__main__':
    main()
