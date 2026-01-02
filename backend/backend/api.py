# backend/api.py
from ninja_extra import NinjaExtraAPI

from core.endpoints import router as core_router
from book.endpoints import router as book_router
from account.endpoints import router as account_router
from ai.endpoints import router as ai_router
from utils.exception_util import register_exception_handlers


api: NinjaExtraAPI = NinjaExtraAPI()

# 注册全局异常处理器
register_exception_handlers(api)

# 注册路由
api.add_router("/", core_router)
api.add_router("/", book_router)
api.add_router("/", account_router)
api.add_router("/", ai_router)
