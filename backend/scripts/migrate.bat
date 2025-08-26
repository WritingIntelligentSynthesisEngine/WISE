cd "../"
start cmd /k .\.venv\Scripts\python.exe .\manage.py makemigrations
start cmd /k .\.venv\Scripts\python.exe .\manage.py migrate
