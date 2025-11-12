cd "../"
start cmd /k docker build --network=host --file wise-backend.Dockerfile --tag knightfemale/wise-backend:latest ./../backend
