#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件推送模块

支持 SCP/SFTP 方式推送到远程服务器。
"""

import os
import paramiko
from scp import SCPClient
from typing import Optional


class FilePusher:
    """文件推送器"""

    def __init__(self, host: str, username: str, password: Optional[str] = None,
                 key_file: Optional[str] = None, port: int = 22):
        self.host = host
        self.username = username
        self.password = password
        self.key_file = key_file
        self.port = port
        self.ssh = None

    def connect(self) -> bool:
        """建立 SSH 连接"""
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if self.key_file and os.path.exists(self.key_file):
                # 使用密钥认证
                pkey = paramiko.RSAKey.from_private_key_file(self.key_file)
                self.ssh.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    pkey=pkey,
                    timeout=30
                )
            elif self.password:
                # 使用密码认证
                self.ssh.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=30
                )
            else:
                print("错误: 未提供密码或密钥文件")
                return False

            print(f"成功连接到 {self.host}")
            return True

        except Exception as e:
            print(f"连接失败: {e}")
            return False

    def push_file(self, local_path: str, remote_path: str) -> bool:
        """推送文件到远程服务器"""
        if not self.ssh:
            print("错误: 未建立连接")
            return False

        try:
            # 确保远程目录存在
            remote_dir = os.path.dirname(remote_path)
            stdin, stdout, stderr = self.ssh.exec_command(f"mkdir -p {remote_dir}")
            stdout.channel.recv_exit_status()

            # 使用 SCP 传输文件
            with SCPClient(self.ssh.get_transport()) as scp:
                scp.put(local_path, remote_path)

            print(f"文件已推送: {local_path} -> {remote_path}")
            return True

        except Exception as e:
            print(f"推送失败: {e}")
            return False

    def close(self):
        """关闭连接"""
        if self.ssh:
            self.ssh.close()
            self.ssh = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main():
    """测试推送功能"""
    import sys

    if len(sys.argv) < 3:
        print("用法: python pusher.py <本地文件> <远程路径>")
        sys.exit(1)

    local_file = sys.argv[1]
    remote_path = sys.argv[2]

    # 从环境变量或配置文件读取服务器信息
    host = os.getenv('REMOTE_HOST', '47.84.177.254')
    username = os.getenv('REMOTE_USER', 'root')
    password = os.getenv('REMOTE_PASSWORD')

    if not password:
        print("错误: 请设置 REMOTE_PASSWORD 环境变量")
        sys.exit(1)

    with FilePusher(host, username, password) as pusher:
        if pusher.push_file(local_file, remote_path):
            print("推送成功")
        else:
            print("推送失败")
            sys.exit(1)


if __name__ == '__main__':
    main()
