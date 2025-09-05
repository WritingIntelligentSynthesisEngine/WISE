# core/api.py
from ninja_extra import NinjaExtraAPI
from ninja_jwt.controller import NinjaJWTDefaultController

from core.routers import router as core_router
from book.routers import router as book_router


api: NinjaExtraAPI = NinjaExtraAPI(title="AllBookCloud API")

# JWT API
api.register_controllers(NinjaJWTDefaultController)
# 服务核心 API
api.add_router("/core", core_router)
# 书籍与文章 API
api.add_router("/book", book_router)
