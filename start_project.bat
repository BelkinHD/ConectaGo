@echo off
echo Starting Docker project in detached mode...
docker-compose up -d
echo Docker project started. Use 'docker-compose logs -f' to view logs.
start http://localhost:8080
