#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
可转债每日推送主程序

每天早上执行：
1. 检查是否为交易日
2. 采集数据
3. 验证数据完整性
4. 生成 CSV
5. 推送到远程服务器

用法:
    python daily_push.py [--check-only] [--local-only]

选项:
    --check-only    仅检查数据，不推送
    --local-only    仅生成本地 CSV，不推送
"""

import os
import sys
import argparse
from datetime import datetime
from collector import CBCollector
from pusher import FilePusher
from data_validator import DataValidator


def check_trade_day() -> bool:
    """检查今天是否为交易日"""
    import requests
    try:
        response = requests.get('http://localhost:5001/api/check-trade-day', timeout=10)
        data = response.json()
        return data.get('is_trade_day', True)
    except Exception as e:
        print(f"交易日检查失败: {e}，默认继续执行")
        return True


def validate_data() -> bool:
    """验证数据完整性"""
    print("\n验证数据完整性...")
    validator = DataValidator()

    if not validator.run_all_validations():
        return False

    summary = validator.get_summary()
    print(f"\n验证结果: {summary['status']}")
    print(f"通过: {summary['pass']}, 警告: {summary['warning']}, 失败: {summary['fail']}")

    # 有失败则阻止推送
    if summary['fail'] > 0:
        print("验证失败，数据完整性有问题，停止推送")
        return False

    return True


def push_to_remote(local_file: str, remote_config: dict) -> bool:
    """推送文件到远程服务器"""
    print(f"\n推送文件到远程服务器...")

    # 构建远程路径（使用前端目录）
    filename = os.path.basename(local_file)
    remote_path = f"{remote_config['remote_path']}/{filename}"

    pusher = FilePusher(
        host=remote_config['host'],
        username=remote_config['username'],
        password=remote_config['password'],
        port=remote_config.get('port', 22)
    )
    return pusher.push_file(local_file, remote_path)


def main():
    parser = argparse.ArgumentParser(description='可转债每日推送')
    parser.add_argument('--check-only', action='store_true', help='仅检查数据，不推送')
    parser.add_argument('--local-only', action='store_true', help='仅生成本地 CSV，不推送')
    parser.add_argument('--skip-trade-check', action='store_true', help='跳过交易日检查')
    parser.add_argument('--skip-validation', action='store_true', help='跳过数据验证')
    args = parser.parse_args()

    print("=" * 60)
    print("可转债每日数据推送")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. 检查交易日
    if not args.skip_trade_check:
        print("\n检查是否为交易日...")
        if not check_trade_day():
            print("今天不是交易日，跳过执行")
            return 0
        print("今天是交易日，继续执行")

    # 2. 采集数据
    print("\n" + "-" * 60)
    collector = CBCollector()
    if not collector.collect_all():
        print("数据采集失败，停止执行")
        return 1

    # 3. 验证数据
    if not args.skip_validation:
        if not validate_data():
            print("数据验证未通过")
            if not args.local_only:
                return 1
    else:
        print("\n跳过数据验证")

    # 4. 合并计算并生成 CSV
    print("\n" + "-" * 60)
    df = collector.merge_and_calculate()
    local_file = collector.save_to_csv(df)

    if args.local_only:
        print("\n仅生成本地文件，不推送")
        print(f"文件路径: {local_file}")
        return 0

    if args.check_only:
        print("\n仅检查数据，不推送")
        return 0

    # 5. 推送到远程
    print("\n" + "-" * 60)
    remote_config = {
        'host': os.getenv('REMOTE_HOST', '47.84.177.254'),
        'username': os.getenv('REMOTE_USER', 'root'),
        'password': os.getenv('REMOTE_PASSWORD'),
        'remote_path': os.getenv('REMOTE_PATH', '/var/www/html/cb_data'),
        'port': int(os.getenv('REMOTE_PORT', '22'))
    }

    if not remote_config['password']:
        print("错误: 未设置 REMOTE_PASSWORD 环境变量")
        return 1

    if push_to_remote(local_file, remote_config):
        print("\n" + "=" * 60)
        print("推送完成!")
        print(f"文件: {os.path.basename(local_file)}")
        print(f"访问: http://{remote_config['host']}/cb_data/{os.path.basename(local_file)}")
        print("=" * 60)
        return 0
    else:
        print("\n推送失败")
        return 1


if __name__ == '__main__':
    sys.exit(main())
