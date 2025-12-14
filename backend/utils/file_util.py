# utils/file_util.py
import os
from hashlib import md5
from pathlib import Path
from typing import Optional

from ninja import UploadedFile
from django.conf import settings

from book.models import Book


def read_text_file(file_path: Path) -> str:
    """读取文本文件内容"""

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"文件 {file_path} 不存在")
    except Exception as e:
        raise Exception(f"读取文件 {file_path} 时出错: {e}")


def save_text_file(file_path: Path, content: str) -> None:
    """保存内容到文本文件"""

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        raise Exception(f"保存文件 {file_path} 时出错: {e}")


def generate_hash_path(file: UploadedFile, depth: int = 2) -> Path:
    """
    基于文件内容哈希生成多级目录路径

    :param file: 上传的文件
    :type file: UploadedFile
    :param depth: 路径前缀
    :type depth: int
    :return: 相对路径
    :rtype: Path
    """

    # 读取文件内容并计算哈希
    file_content: bytes = b"".join([chunk for chunk in file.chunks()])
    file_hash: str = md5(file_content).hexdigest()
    # 构造多级哈希目录
    hash_based_path: Path = Path()
    for i in range(depth):
        start_index = i * 2
        end_index = start_index + 2
        hash_based_path: Path = hash_based_path / Path(file_hash[start_index:end_index])
    # 返回路径
    return hash_based_path / Path(f"{file_hash}{os.path.splitext(file.name)[1]}")


def save_static_file(file: Optional[UploadedFile], root_path: Path = settings.MEDIA_ROOT, subdirectory: str = "") -> str:
    """
    保存静态文件到指定根路径

    :param file: 上传的文件
    :type file: Optional[UploadedFile]
    :param root_path: 根目录路径
    :type root_path: Path
    :param subdirectory: 子目录名称
    :type subdirectory: str
    :return: 相对于根目录的文件路径
    :rtype: str
    """

    # 如果没有文件则直接返回空字符串
    if file is None:
        return ""
    # 生成基于哈希的路径
    file_path: Path = generate_hash_path(file)
    # 构造完整路径
    if subdirectory:
        full_path: Path = root_path / Path(subdirectory) / file_path
    else:
        full_path: Path = root_path / file_path
    # 确保目录存在
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    # 只有在文件不存在时才保存
    if not os.path.exists(full_path):
        with open(full_path, "wb+") as destination:
            for chunk in file.chunks():
                destination.write(chunk)
    return str(file_path)


def remove_static_file(
    file_path: str,
    root_path: Path = settings.MEDIA_ROOT,
    subdirectory: str = "",
) -> None:
    """
    删除静态文件的物理文件

    :param file_path: 相对文件路径
    :type file_path: str
    :param root_path: 根目录路径
    :type root_path: Path
    :param subdirectory: 子目录名称
    :type subdirectory: str
    """

    # 如果没有文件路径则直接退出
    if not file_path:
        return
    try:
        # 构造完整路径
        if subdirectory:
            full_path: Path = root_path / Path(subdirectory) / Path(file_path)
        else:
            full_path: Path = root_path / Path(file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            # 尝试删除可能的空目录
            try:
                os.removedirs(os.path.dirname(full_path))
            except OSError:
                # 目录不为空或无法删除, 忽略错误
                pass
    except (OSError, FileNotFoundError):
        # 文件删除失败, 记录日志或忽略
        pass


def save_cover_image(cover_image: Optional[UploadedFile]) -> str:
    """保存封面图片"""

    return save_static_file(cover_image, subdirectory="covers")


def remove_unused_cover_image(cover_image_path: str) -> None:
    """
    检查封面图片是否被其他书籍引用, 如果没有则删除物理文件

    调用此函数前, 当前书籍应当已经删除了该引用(删除了书籍记录或清空了字段)
    """

    is_cited_by_others: bool = Book.objects.filter(cover_image_path=cover_image_path).exists()
    if not is_cited_by_others:
        remove_static_file(cover_image_path, subdirectory="covers")
