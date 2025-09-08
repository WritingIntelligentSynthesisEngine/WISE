# utils/path_util.py
import os
import hashlib
from pathlib import Path

from ninja import UploadedFile


def generate_hash_path(file: UploadedFile, depth: int = 2) -> Path:
    """基于文件内容哈希生成多级目录路径

    参数:
        file: 上传的文件
        prefix: 路径前缀
        depth: 目录层级深度

    返回:
        Path: 相对路径
    """
    # 读取文件内容并计算哈希
    file_content: bytes = b"".join([chunk for chunk in file.chunks()])
    file_hash: str = hashlib.md5(file_content).hexdigest()
    # 构造多级哈希目录
    hash_based_path: Path = Path()
    for i in range(depth):
        start_index = i * 2
        end_index = start_index + 2
        hash_based_path: Path = hash_based_path / Path(file_hash[start_index:end_index])
    # 返回路径
    return hash_based_path / Path(f"{file_hash}{os.path.splitext(file.name)[1]}")
