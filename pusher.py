#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件推送模块

使用 rsync 推送到远程服务器（比 SCP 更稳定，支持断点续传）。
"""

import os
import subprocess
from typing import Optional


class FilePusher:
    """文件推送器（使用 rsync）"""

    def __init__(self, host: str, username: str, password: Optional[str] = None,
                 key_file: Optional[str] = None, port: int = 22):
        self.host = host
        self.username = username
        self.password = password
        self.key_file = key_file
        self.port = port

    def _build_rsync_cmd(self, local_path: str, remote_path: str) -> list:
        """构建 rsync 命令"""
        # 基础选项
        # -a: 归档模式
        # -v: 详细输出
        # -z: 压缩传输
        # --timeout=60: 超时 60 秒
        # --partial: 断点续传
        # --progress: 显示进度
        cmd = [
            'rsync',
            '-avz',
            '--timeout=60',
            '--partial',
            '-e', f'ssh -p {self.port} -o StrictHostKeyChecking=no -o ConnectTimeout=30'
        ]

        # 添加密钥或密码认证
        if self.key_file and os.path.exists(self.key_file):
            cmd[-1] += f' -i {self.key_file}'

        # 构建目标路径
        remote_full = f"{self.username}@{self.host}:{remote_path}"

        cmd.extend([local_path, remote_full])
        return cmd

    def push_file(self, local_path: str, remote_path: str) -> bool:
        """推送文件到远程服务器"""
        if not os.path.exists(local_path):
            print(f"错误: 本地文件不存在: {local_path}")
            return False

        try:
            # 确保远程目录存在（使用 ssh）
            remote_dir = os.path.dirname(remote_path)
            mkdir_cmd = [
                'ssh',
                '-p', str(self.port),
                '-o', 'StrictHostKeyChecking=no',
                '-o', 'ConnectTimeout=30',
                f'{self.username}@{self.host}',
                f'mkdir -p {remote_dir}'
            ]

            # 如果需要密码，使用 sshpass
            if self.password and not self.key_file:
                # 检查是否有 sshpass
                try:
                    subprocess.run(['which', 'sshpass'], check=True, capture_output=True)
                    mkdir_cmd = ['sshpass', '-p', self.password] + mkdir_cmd
                except subprocess.CalledProcessError:
                    print("警告: 未安装 sshpass，无法使用密码认证")
                    print("建议: 使用 SSH 密钥认证，或安装 sshpass: brew install sshpass")
                    return False

            result = subprocess.run(
                mkdir_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                print(f"创建远程目录失败: {result.stderr}")
                return False

            # 构建并执行 rsync 命令
            rsync_cmd = self._build_rsync_cmd(local_path, remote_path)

            if self.password and not self.key_file:
                try:
                    subprocess.run(['which', 'sshpass'], check=True, capture_output=True)
                    rsync_cmd = ['sshpass', '-p', self.password] + rsync_cmd
                except subprocess.CalledProcessError:
                    pass  # 已经检查过了

            print(f"执行: {' '.join(rsync_cmd[:5])} ...")  # 只显示部分命令（隐藏密码）

            result = subprocess.run(
                rsync_cmd,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                print(f"✓ 文件已推送: {os.path.basename(local_path)} -> {self.host}:{remote_path}")
                return True
            else:
                print(f"推送失败: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("错误: rsync 执行超时")
            return False
        except Exception as e:
            print(f"推送失败: {e}")
            return False


class SCPPusher(FilePusher):
    """兼容旧代码：SCP 推送器（备用）"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("警告: SCPPusher 已弃用，使用 FilePusher (rsync) 替代")


def main():
    """测试推送功能"""
    import sys

    if len(sys.argv) < 3:
        print("用法: python pusher.py <本地文件> <远程路径>")
        print("示例: python pusher.py output/cb_data.csv /var/www/html/cb_data/")
        sys.exit(1)

    local_file = sys.argv[1]
    remote_path = sys.argv[2]

    # 从环境变量读取服务器信息
    host = os.getenv('REMOTE_HOST', '47.84.177.254')
    username = os.getenv('REMOTE_USER', 'root')
    password = os.getenv('REMOTE_PASSWORD')
    key_file = os.getenv('REMOTE_KEY_FILE')

    if not password and not key_file:
        print("错误: 请设置 REMOTE_PASSWORD 或 REMOTE_KEY_FILE 环境变量")
        sys.exit(1)

    pusher = FilePusher(host, username, password, key_file)

    if pusher.push_file(local_file, remote_path):
        print("✓ 推送成功")
    else:
        print("✗ 推送失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
