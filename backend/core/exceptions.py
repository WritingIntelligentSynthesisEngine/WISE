# core/exceptions.py
class CoreException(Exception):
    """核心异常基类"""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
