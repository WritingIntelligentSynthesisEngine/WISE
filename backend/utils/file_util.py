from pathlib import Path


def read_file(file_path: Path) -> str:
    """读取文件内容"""

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"文件 {file_path} 不存在")
    except Exception as e:
        raise Exception(f"读取文件 {file_path} 时出错: {e}")


def save_file(file_path: Path, content: str) -> None:
    """保存内容到文件"""

    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        raise Exception(f"保存文件 {file_path} 时出错: {e}")
