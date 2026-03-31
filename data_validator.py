#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可转债数据采集验证程序

每天数据采集后运行此程序，验证数据完整性和一致性。

使用方法:
    python data_validator.py [--json] [--save-report]

选项:
    --json          以 JSON 格式输出结果
    --save-report   保存验证报告到 reports/ 目录
"""

import sys
import json
import argparse
import requests
from datetime import datetime, date
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import os


class ValidationStatus(Enum):
    """验证状态"""
    PASS = "通过"
    FAIL = "失败"
    WARNING = "警告"


@dataclass
class ValidationResult:
    """单个验证项的结果"""
    name: str
    status: ValidationStatus
    message: str
    details: Dict[str, Any] = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}

    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'status': self.status.value,
            'message': self.message,
            'details': self.details
        }


class DataValidator:
    """数据采集验证器"""

    # API 端点配置
    BASE_URL = "http://localhost:5001"
    ENDPOINTS = {
        'check_trade_day': '/api/check-trade-day',
        'cb_list': '/api/cb-list',
        'stock_data': '/api/stock-data',
        'controller': '/api/controller',
        'finance': '/api/finance'
    }

    # 验证阈值配置
    THRESHOLDS = {
        'min_cb_count': 350,           # 可转债最小数量
        'expected_cb_count': 355,       # 预期可转债数量
        'min_stock_coverage': 0.95,     # 正股数据最小覆盖率
        'min_controller_coverage': 0.90, # 股东数据最小覆盖率
        'min_finance_coverage': 0.85,    # 财务数据最小覆盖率
        'max_missing_ratio': 0.10,       # 最大缺失字段比例
    }

    # 关键字段配置
    REQUIRED_CB_FIELDS = [
        '转债代码', '转债名称', '正股代码', '正股名称',
        '转股价格', '当前股价', '可转债剩余规模'
    ]

    REQUIRED_STOCK_FIELDS = ['正股代码', '正股名称', '当前股价', 'PB']
    REQUIRED_CONTROLLER_FIELDS = ['正股代码', '实际控制人']
    REQUIRED_FINANCE_FIELDS = ['正股代码']

    def __init__(self, base_url: str = None):
        self.base_url = base_url or self.BASE_URL
        self.results: List[ValidationResult] = []
        self.collected_data: Dict[str, Any] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def _api_call(self, endpoint: str) -> Tuple[bool, Dict]:
        """调用 API 并返回结果"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get('success', False), data
        except Exception as e:
            return False, {'error': str(e)}

    def _add_result(self, name: str, status: ValidationStatus, message: str, details: Dict = None):
        """添加验证结果"""
        result = ValidationResult(name, status, message, details)
        self.results.append(result)

        if status == ValidationStatus.FAIL:
            self.errors.append(f"[{name}] {message}")
        elif status == ValidationStatus.WARNING:
            self.warnings.append(f"[{name}] {message}")

    def validate_api_health(self) -> bool:
        """验证 API 服务健康状态"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                self._add_result(
                    "API健康检查",
                    ValidationStatus.PASS,
                    "API 服务运行正常",
                    {'status_code': response.status_code}
                )
                return True
            else:
                self._add_result(
                    "API健康检查",
                    ValidationStatus.FAIL,
                    f"API 返回非200状态码: {response.status_code}",
                    {'status_code': response.status_code}
                )
                return False
        except Exception as e:
            self._add_result(
                "API健康检查",
                ValidationStatus.FAIL,
                f"无法连接 API 服务: {str(e)}",
                {'error': str(e)}
            )
            return False

    def validate_trade_day_check(self) -> bool:
        """验证交易日检查功能"""
        success, data = self._api_call(self.ENDPOINTS['check_trade_day'])

        if not success:
            self._add_result(
                "交易日检查",
                ValidationStatus.FAIL,
                f"交易日检查失败: {data.get('error', '未知错误')}",
                data
            )
            return False

        today = datetime.now().strftime('%Y%m%d')
        is_trade_day = data.get('is_trade_day', False)

        self.collected_data['is_trade_day'] = is_trade_day
        self.collected_data['today'] = data.get('today', today)

        self._add_result(
            "交易日检查",
            ValidationStatus.PASS,
            f"今天是{data.get('today', today)}，{'交易日' if is_trade_day else '非交易日'}",
            {'is_trade_day': is_trade_day, 'today': data.get('today', today)}
        )
        return True

    def validate_cb_list(self) -> bool:
        """验证可转债列表数据"""
        success, data = self._api_call(self.ENDPOINTS['cb_list'])

        if not success:
            self._add_result(
                "可转债列表",
                ValidationStatus.FAIL,
                f"获取可转债列表失败: {data.get('error', '未知错误')}",
                data
            )
            return False

        cb_list = data.get('cb_list', [])
        count = len(cb_list)

        self.collected_data['cb_list'] = cb_list
        self.collected_data['cb_count'] = count

        # 检查数量
        if count == 0:
            self._add_result(
                "可转债列表-数量",
                ValidationStatus.FAIL,
                "可转债列表为空",
                {'count': count}
            )
            return False

        if count < self.THRESHOLDS['min_cb_count']:
            self._add_result(
                "可转债列表-数量",
                ValidationStatus.WARNING,
                f"可转债数量({count})低于阈值({self.THRESHOLDS['min_cb_count']})",
                {'count': count, 'threshold': self.THRESHOLDS['min_cb_count']}
            )
        else:
            self._add_result(
                "可转债列表-数量",
                ValidationStatus.PASS,
                f"可转债数量: {count} 条",
                {'count': count, 'expected': self.THRESHOLDS['expected_cb_count']}
            )

        # 检查必填字段
        if cb_list:
            missing_fields = []
            sample = cb_list[0]
            for field in self.REQUIRED_CB_FIELDS:
                if field not in sample:
                    missing_fields.append(field)

            if missing_fields:
                self._add_result(
                    "可转债列表-字段",
                    ValidationStatus.FAIL,
                    f"缺少关键字段: {', '.join(missing_fields)}",
                    {'missing_fields': missing_fields, 'available_fields': list(sample.keys())}
                )
            else:
                # 检查字段缺失率
                total_fields = len(self.REQUIRED_CB_FIELDS) * count
                missing_count = 0
                for cb in cb_list:
                    for field in self.REQUIRED_CB_FIELDS:
                        if field not in cb or cb[field] is None or cb[field] == '':
                            missing_count += 1

                missing_ratio = missing_count / total_fields if total_fields > 0 else 0

                if missing_ratio > self.THRESHOLDS['max_missing_ratio']:
                    self._add_result(
                        "可转债列表-字段完整性",
                        ValidationStatus.WARNING,
                        f"字段缺失率过高: {missing_ratio:.2%}",
                        {'missing_ratio': missing_ratio, 'threshold': self.THRESHOLDS['max_missing_ratio']}
                    )
                else:
                    self._add_result(
                        "可转债列表-字段完整性",
                        ValidationStatus.PASS,
                        f"字段完整性良好，缺失率: {missing_ratio:.2%}",
                        {'missing_ratio': missing_ratio}
                    )

        # 检查数据合理性
        invalid_items = []
        for cb in cb_list[:50]:  # 只检查前50条
            issues = []
            if not cb.get('转债代码') or len(str(cb.get('转债代码', ''))) < 5:
                issues.append("转债代码无效")
            if not cb.get('正股代码') or len(str(cb.get('正股代码', ''))) < 5:
                issues.append("正股代码无效")

            price = cb.get('当前股价')
            if price is not None and (price <= 0 or price > 10000):
                issues.append(f"股价异常({price})")

            if issues:
                invalid_items.append({
                    'code': cb.get('转债代码', 'unknown'),
                    'name': cb.get('转债名称', 'unknown'),
                    'issues': issues
                })

        if invalid_items:
            self._add_result(
                "可转债列表-数据合理性",
                ValidationStatus.WARNING,
                f"发现 {len(invalid_items)} 条数据异常",
                {'sample_issues': invalid_items[:5]}
            )
        else:
            self._add_result(
                "可转债列表-数据合理性",
                ValidationStatus.PASS,
                "数据合理性检查通过",
                {'checked_count': min(50, count)}
            )

        return True

    def validate_stock_data(self) -> bool:
        """验证正股数据"""
        success, data = self._api_call(self.ENDPOINTS['stock_data'])

        if not success:
            self._add_result(
                "正股数据",
                ValidationStatus.FAIL,
                f"获取正股数据失败: {data.get('error', '未知错误')}",
                data
            )
            return False

        spot = data.get('spot', [])
        ma = data.get('ma', [])

        self.collected_data['stock_spot'] = spot
        self.collected_data['stock_ma'] = ma

        if not spot:
            self._add_result(
                "正股数据-数量",
                ValidationStatus.FAIL,
                "正股数据为空",
                {'count': 0}
            )
            return False

        spot_count = len(spot)
        cb_count = self.collected_data.get('cb_count', 0)

        self._add_result(
            "正股数据-数量",
            ValidationStatus.PASS,
            f"正股数据: {spot_count} 条",
            {'count': spot_count}
        )

        # 检查字段
        if spot:
            sample = spot[0]
            missing_fields = [f for f in self.REQUIRED_STOCK_FIELDS if f not in sample]
            if missing_fields:
                self._add_result(
                    "正股数据-字段",
                    ValidationStatus.WARNING,
                    f"缺少字段: {', '.join(missing_fields)}",
                    {'missing_fields': missing_fields}
                )
            else:
                self._add_result(
                    "正股数据-字段",
                    ValidationStatus.PASS,
                    "关键字段完整",
                    {'fields': list(sample.keys())[:10]}
                )

        return True

    def validate_controller_data(self) -> bool:
        """验证股东数据"""
        success, data = self._api_call(self.ENDPOINTS['controller'])

        if not success:
            self._add_result(
                "股东数据",
                ValidationStatus.FAIL,
                f"获取股东数据失败: {data.get('error', '未知错误')}",
                data
            )
            return False

        controller_data = data.get('controller_data', [])
        self.collected_data['controller_data'] = controller_data

        if not controller_data:
            self._add_result(
                "股东数据-数量",
                ValidationStatus.FAIL,
                "股东数据为空",
                {'count': 0}
            )
            return False

        count = len(controller_data)
        cb_count = self.collected_data.get('cb_count', 0)

        # 检查覆盖率
        if cb_count > 0:
            coverage = count / cb_count
            if coverage < self.THRESHOLDS['min_controller_coverage']:
                self._add_result(
                    "股东数据-覆盖率",
                    ValidationStatus.WARNING,
                    f"覆盖率 {coverage:.1%} 低于阈值 {self.THRESHOLDS['min_controller_coverage']:.1%}",
                    {'coverage': coverage, 'count': count, 'expected': cb_count}
                )
            else:
                self._add_result(
                    "股东数据-覆盖率",
                    ValidationStatus.PASS,
                    f"覆盖率 {coverage:.1%} ({count}/{cb_count})",
                    {'coverage': coverage}
                )
        else:
            self._add_result(
                "股东数据-数量",
                ValidationStatus.PASS,
                f"股东数据: {count} 条",
                {'count': count}
            )

        return True

    def validate_finance_data(self) -> bool:
        """验证财务数据"""
        success, data = self._api_call(self.ENDPOINTS['finance'])

        if not success:
            self._add_result(
                "财务数据",
                ValidationStatus.FAIL,
                f"获取财务数据失败: {data.get('error', '未知错误')}",
                data
            )
            return False

        finance_data = data.get('finance_data', [])
        self.collected_data['finance_data'] = finance_data

        if not finance_data:
            self._add_result(
                "财务数据-数量",
                ValidationStatus.FAIL,
                "财务数据为空",
                {'count': 0}
            )
            return False

        count = len(finance_data)
        cb_count = self.collected_data.get('cb_count', 0)

        # 检查覆盖率
        if cb_count > 0:
            coverage = count / cb_count
            if coverage < self.THRESHOLDS['min_finance_coverage']:
                self._add_result(
                    "财务数据-覆盖率",
                    ValidationStatus.WARNING,
                    f"覆盖率 {coverage:.1%} 低于阈值 {self.THRESHOLDS['min_finance_coverage']:.1%}",
                    {'coverage': coverage, 'count': count, 'expected': cb_count}
                )
            else:
                self._add_result(
                    "财务数据-覆盖率",
                    ValidationStatus.PASS,
                    f"覆盖率 {coverage:.1%} ({count}/{cb_count})",
                    {'coverage': coverage}
                )
        else:
            self._add_result(
                "财务数据-数量",
                ValidationStatus.PASS,
                f"财务数据: {count} 条",
                {'count': count}
            )

        # 检查财务数据有效性
        valid_cash_count = sum(1 for f in finance_data if f.get('期末现金余额') is not None)

        if count > 0:
            valid_ratio = valid_cash_count / count
            if valid_ratio < 0.5:
                self._add_result(
                    "财务数据-有效性",
                    ValidationStatus.WARNING,
                    f"有效财务数据比例较低: {valid_ratio:.1%}",
                    {'valid_ratio': valid_ratio, 'valid_count': valid_cash_count}
                )
            else:
                self._add_result(
                    "财务数据-有效性",
                    ValidationStatus.PASS,
                    f"有效财务数据: {valid_cash_count}/{count} ({valid_ratio:.1%})",
                    {'valid_ratio': valid_ratio}
                )

        return True

    def validate_data_consistency(self) -> bool:
        """验证数据一致性"""
        cb_list = self.collected_data.get('cb_list', [])
        controller_data = self.collected_data.get('controller_data', [])
        finance_data = self.collected_data.get('finance_data', [])
        stock_spot = self.collected_data.get('stock_spot', [])

        if not cb_list:
            self._add_result(
                "数据一致性",
                ValidationStatus.FAIL,
                "无可转债列表数据，无法检查一致性"
            )
            return False

        # 提取正股代码集合
        cb_stock_codes = {item.get('正股代码') for item in cb_list if item.get('正股代码')}
        controller_codes = {item.get('正股代码') for item in controller_data if item.get('正股代码')}
        finance_codes = {item.get('正股代码') for item in finance_data if item.get('正股代码')}
        spot_codes = {item.get('正股代码') for item in stock_spot if item.get('正股代码')}

        # 检查各数据集的覆盖情况
        consistency_results = []

        # 正股数据覆盖
        if spot_codes:
            spot_coverage = len(cb_stock_codes & spot_codes) / len(cb_stock_codes) if cb_stock_codes else 0
            consistency_results.append({
                'name': '正股行情',
                'coverage': spot_coverage,
                'covered': len(cb_stock_codes & spot_codes),
                'total': len(cb_stock_codes)
            })

        # 股东数据覆盖
        if controller_codes:
            controller_coverage = len(cb_stock_codes & controller_codes) / len(cb_stock_codes) if cb_stock_codes else 0
            consistency_results.append({
                'name': '股东信息',
                'coverage': controller_coverage,
                'covered': len(cb_stock_codes & controller_codes),
                'total': len(cb_stock_codes)
            })

        # 财务数据覆盖
        if finance_codes:
            finance_coverage = len(cb_stock_codes & finance_codes) / len(cb_stock_codes) if cb_stock_codes else 0
            consistency_results.append({
                'name': '财务数据',
                'coverage': finance_coverage,
                'covered': len(cb_stock_codes & finance_codes),
                'total': len(cb_stock_codes)
            })

        # 检查重复数据
        cb_codes_list = [item.get('转债代码') for item in cb_list if item.get('转债代码')]
        duplicates = [code for code in set(cb_codes_list) if cb_codes_list.count(code) > 1]

        if duplicates:
            self._add_result(
                "数据一致性-重复检查",
                ValidationStatus.WARNING,
                f"发现 {len(duplicates)} 个重复的转债代码",
                {'duplicates': duplicates[:10]}
            )
        else:
            self._add_result(
                "数据一致性-重复检查",
                ValidationStatus.PASS,
                "无重复数据",
                {'total_items': len(cb_codes_list), 'unique_items': len(set(cb_codes_list))}
            )

        # 汇总一致性结果
        if consistency_results:
            avg_coverage = sum(r['coverage'] for r in consistency_results) / len(consistency_results)

            if avg_coverage < 0.8:
                status = ValidationStatus.WARNING
            else:
                status = ValidationStatus.PASS

            self._add_result(
                "数据一致性-覆盖率汇总",
                status,
                f"平均覆盖率: {avg_coverage:.1%}",
                {'details': consistency_results, 'average_coverage': avg_coverage}
            )

        return True

    def run_all_validations(self) -> bool:
        """运行所有验证"""
        print("=" * 60)
        print("可转债数据采集验证程序")
        print(f"验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # 1. API 健康检查
        print("\n[1/7] 检查 API 服务健康状态...")
        if not self.validate_api_health():
            print("  ✗ API 服务不可用，终止验证")
            return False
        print("  ✓ API 服务正常")

        # 2. 交易日检查
        print("\n[2/7] 检查交易日...")
        self.validate_trade_day_check()

        # 3. 可转债列表
        print("\n[3/7] 验证可转债列表...")
        if not self.validate_cb_list():
            print("  ✗ 可转债列表验证失败")
        else:
            print(f"  ✓ 可转债列表: {self.collected_data.get('cb_count', 0)} 条")

        # 4. 正股数据
        print("\n[4/7] 验证正股数据...")
        self.validate_stock_data()

        # 5. 股东数据
        print("\n[5/7] 验证股东数据...")
        self.validate_controller_data()

        # 6. 财务数据
        print("\n[6/7] 验证财务数据...")
        self.validate_finance_data()

        # 7. 数据一致性
        print("\n[7/7] 验证数据一致性...")
        self.validate_data_consistency()

        return True

    def get_summary(self) -> Dict:
        """获取验证摘要"""
        pass_count = sum(1 for r in self.results if r.status == ValidationStatus.PASS)
        warning_count = sum(1 for r in self.results if r.status == ValidationStatus.WARNING)
        fail_count = sum(1 for r in self.results if r.status == ValidationStatus.FAIL)

        overall_status = "通过" if fail_count == 0 else "失败"
        if warning_count > 0 and fail_count == 0:
            overall_status = "通过(有警告)"

        return {
            'status': overall_status,
            'total': len(self.results),
            'pass': pass_count,
            'warning': warning_count,
            'fail': fail_count,
            'timestamp': datetime.now().isoformat(),
            'is_trade_day': self.collected_data.get('is_trade_day', True),
            'today': self.collected_data.get('today', datetime.now().strftime('%Y%m%d')),
            'cb_count': self.collected_data.get('cb_count', 0)
        }

    def print_report(self):
        """打印验证报告"""
        print("\n" + "=" * 60)
        print("验证结果汇总")
        print("=" * 60)

        summary = self.get_summary()

        print(f"\n总体状态: {summary['status']}")
        print(f"验证时间: {summary['timestamp']}")
        print(f"交易日: {'是' if summary['is_trade_day'] else '否'}")
        print(f"可转债数量: {summary['cb_count']}")
        print(f"\n通过: {summary['pass']} | 警告: {summary['warning']} | 失败: {summary['fail']}")

        print("\n" + "-" * 60)
        print("详细结果:")
        print("-" * 60)

        for result in self.results:
            icon = "✓" if result.status == ValidationStatus.PASS else "⚠" if result.status == ValidationStatus.WARNING else "✗"
            print(f"\n{icon} [{result.status.value}] {result.name}")
            print(f"   {result.message}")

        if self.errors:
            print("\n" + "!" * 60)
            print("错误列表:")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print("\n" + "⚠" * 30)
            print("警告列表:")
            for warning in self.warnings:
                print(f"  - {warning}")

        print("\n" + "=" * 60)

    def save_report(self, directory: str = "reports") -> str:
        """保存验证报告到文件"""
        os.makedirs(directory, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"validation_report_{timestamp}.json"
        filepath = os.path.join(directory, filename)

        report = {
            'summary': self.get_summary(),
            'results': [r.to_dict() for r in self.results],
            'data_sample': {
                'cb_count': self.collected_data.get('cb_count', 0),
                'stock_count': len(self.collected_data.get('stock_spot', [])),
                'controller_count': len(self.collected_data.get('controller_data', [])),
                'finance_count': len(self.collected_data.get('finance_data', []))
            }
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return filepath

    def to_json(self) -> str:
        """返回 JSON 格式的验证结果"""
        report = {
            'summary': self.get_summary(),
            'results': [r.to_dict() for r in self.results]
        }
        return json.dumps(report, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description='可转债数据采集验证程序')
    parser.add_argument('--json', action='store_true', help='以 JSON 格式输出')
    parser.add_argument('--save-report', action='store_true', help='保存验证报告')
    parser.add_argument('--api-url', default='http://localhost:5001', help='API 基础 URL')

    args = parser.parse_args()

    # 创建验证器
    validator = DataValidator(base_url=args.api_url)

    # 运行验证
    success = validator.run_all_validations()

    if not success:
        if args.json:
            print(json.dumps({'status': '失败', 'error': 'API 服务不可用'}, ensure_ascii=False))
        sys.exit(1)

    # 输出结果
    if args.json:
        print(validator.to_json())
    else:
        validator.print_report()

    # 保存报告
    if args.save_report:
        filepath = validator.save_report()
        print(f"\n报告已保存: {filepath}")

    # 根据验证结果退出
    summary = validator.get_summary()
    if summary['fail'] > 0:
        sys.exit(1)
    elif summary['warning'] > 0:
        sys.exit(2)  # 有警告但不算失败
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
