cd "../"
start cmd /k .\.venv\Scripts\python.exe .\manage.py startapp %1 --template=./templates/app_template
