# main.py
import os
import uvicorn
from dotenv import load_dotenv


def main() -> None:
    uvicorn.run(
        "backend.asgi:application",
        host="0.0.0.0",
        port=30001,
        workers=int(os.environ.get("BACKEND_WORKERS", 1)),
        reload=False,
    )


if __name__ == "__main__":
    load_dotenv()
    main()
