@echo off
echo Starting Contract Intelligence System...
echo.

echo Checking Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not in PATH
    echo Please install Docker Desktop from https://docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo Starting all services with Docker Compose...
docker-compose down
docker-compose up --build

echo.
echo Services should be available at:
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
pause
