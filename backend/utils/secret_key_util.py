# utils/secret_key_util.py
import secrets
from typing import Set


def generate_safe_secret_key(min_length=50) -> str:
    """生成一个不包含特殊字符的安全密钥

    参数:
        min_length: 密钥的最小长度

    返回:
        str: 一个安全的密钥字符串
    """
    # 定义需要排除的特殊字符(这些字符在 Shell 环境变量中可能有特殊含义)
    unsafe_chars: Set = set("$`\"'\\|&;<>()[]{}!^*%?#~=+\t\n\r")
    # 无限尝试生成安全密钥
    while True:
        # 生成一个随机密钥
        key: str = secrets.token_urlsafe(min_length)
        # 检查是否包含任何不安全字符
        if not any(char in unsafe_chars for char in key):
            return key


if __name__ == "__main__":
    print(generate_safe_secret_key())
