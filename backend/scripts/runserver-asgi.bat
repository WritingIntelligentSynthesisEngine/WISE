:: scripts/runserver-asgi.bat
set BACKEND_DEBUG=False
cd "../"
start cmd /k .\.venv\Scripts\python.exe .\main.py
