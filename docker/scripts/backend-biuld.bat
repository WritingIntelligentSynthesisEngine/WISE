cd "../"
start cmd /k docker build --network=host --file backend.Dockerfile --tag knightfemale/backend:latest ./../backend
