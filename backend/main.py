# main.py
import uvicorn
import multiprocessing
from dotenv import load_dotenv


def main() -> None:
    load_dotenv()
    uvicorn.run(
        "core.asgi:application",
        host="0.0.0.0",
        port=30001,
        workers=multiprocessing.cpu_count(),
        reload=False,
    )


if __name__ == "__main__":
    main()
