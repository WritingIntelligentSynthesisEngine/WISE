# main.py
import uvicorn
import multiprocessing


def main() -> None:
    uvicorn.run(
        "backend.asgi:application",
        host="0.0.0.0",
        port=30001,
        workers=multiprocessing.cpu_count(),
        reload=False,
    )


if __name__ == "__main__":
    main()
