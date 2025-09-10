:: scripts/runserver-asgi.bat
set BACKEND_DEBUG=False
set EMAIL_HOST_USER=
set EMAIL_HOST_PASSWORD=
cd "../"
start cmd /k .\.venv\Scripts\python.exe .\main.py
