# utils/log_util.py
import os
import logging
from typing import Dict
from pathlib import Path
from logging import FileHandler, Formatter, Logger, StreamHandler, handlers


# 全局标志
_logging_initialized: bool = False

# 存储任务日志处理器的字典
_task_handlers: Dict[str, FileHandler] = {}


def setup_logging(log_level: int = logging.INFO) -> None:
    """配置全局日志系统"""
    global _logging_initialized
    # 确保只初始化一次
    if _logging_initialized:
        return
    # 创建日志目录(确保存在)
    log_dir: str = "./logs"
    os.makedirs(log_dir, exist_ok=True)
    # 定义统一日志格式
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter: Formatter = logging.Formatter(log_format)
    # 配置根日志记录器
    root_logger: Logger = logging.getLogger()
    root_logger.setLevel(log_level)
    # 添加控制台处理器(标准输出)
    console_handler: StreamHandler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    # 添加文件处理器(滚动日志, 只记录 WARNING 及以上级别)
    file_handler: handlers.RotatingFileHandler = handlers.RotatingFileHandler(
        # 文件目录
        filename=os.path.join(log_dir, "app.log"),
        # 文件大小限制 10 MB
        maxBytes=10 * 1024 * 1024,
        # 保留5个备份
        backupCount=5,
        # 支持中文
        encoding="utf-8",
    )
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    # 设置标志(已在全局作用域申明)
    _logging_initialized = True
    # 记录初始化信息
    root_logger.info("📝日志系统初始化完成, 日志级别设置为: %s", logging.getLevelName(log_level))


def setup_specific_logger(logger_name: str, log_dir: Path) -> logging.Logger:
    """设置特定的日志记录器"""
    # 创建日志目录
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file: Path = log_dir / f"{logger_name}.log"
    # 创建特定的日志记录器
    task_logger: Logger = logging.getLogger(logger_name)
    task_logger.setLevel(logging.INFO)
    # 禁止日志传播到父记录器
    task_logger.propagate = False
    # 创建文件处理器
    file_handler: logging.FileHandler = logging.FileHandler(log_file, encoding="utf-8")
    # 定义统一日志格式
    log_format: str = "%(asctime)s - %(levelname)s - %(message)s"
    formatter: Formatter = logging.Formatter(log_format)
    file_handler.setFormatter(formatter)
    # 添加处理器
    task_logger.addHandler(file_handler)
    # 存储处理器以便后续清理
    _task_handlers[logger_name] = file_handler
    return task_logger


def cleanup_specific_logger(logger_name: str) -> None:
    """清理任务日志处理器"""
    if logger_name in _task_handlers:
        task_logger: Logger = logging.getLogger(logger_name)
        handler: FileHandler = _task_handlers[logger_name]
        # 移除处理器并关闭
        task_logger.removeHandler(handler)
        handler.close()
        # 从字典中移除
        del _task_handlers[logger_name]
