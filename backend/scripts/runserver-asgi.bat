:: scripts/runserver-asgi.bat
set SECRET_KEY=
set BACKEND_DEBUG=False
cd "../"
start cmd /k .\.venv\Scripts\python.exe .\main.py
