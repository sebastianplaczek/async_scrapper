@echo off
cd /d "%~dp0"
docker-compose up
timeout /t 10 /nobreak