:: scripts/runserver.bat
set EMAIL_HOST_USER=
set EMAIL_HOST_PASSWORD=
cd "../"
start cmd /k .\.venv\Scripts\python.exe .\manage.py runserver 0.0.0.0:30001
