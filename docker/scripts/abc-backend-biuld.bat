cd "../"
start cmd /k docker build --network=host --file abc-backend.Dockerfile --tag knightfemale/abc-backend:latest ./../backend
