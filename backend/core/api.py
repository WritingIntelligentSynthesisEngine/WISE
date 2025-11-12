# core/api.py
from ninja_extra import NinjaExtraAPI

from core.routers import router as core_router
from account.routers import router as account_router
from book.routers import router as book_router


api: NinjaExtraAPI = NinjaExtraAPI(title="WISE API")

# 服务核心 API
api.add_router("/core", core_router)
# 账户 API
api.add_router("/account", account_router)
# 书籍与文章 API
api.add_router("/book", book_router)
