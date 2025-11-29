# ai/exceptions.py
class AiException(Exception):
    """AI 异常基类"""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
