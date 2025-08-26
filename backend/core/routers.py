# core/routers.py
from typing import Any

from ninja import Router

router: Router = Router()


@router.get("/hello")
def hello(request: Any) -> str:
    return "Hello World!"
