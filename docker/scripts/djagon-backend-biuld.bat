cd "../"
start cmd /k docker build --network=host --file djagon-backend.Dockerfile --tag knightfemale/djagon-backend:latest ./../backend
