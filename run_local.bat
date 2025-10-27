@echo off
echo 🏠 Starting KaTek Real Estate Platform (Local Development)
echo ============================================================

REM Set development environment
set DEBUG=True
set ALLOWED_HOSTS=localhost,127.0.0.1

REM Check if manage.py exists
if not exist "manage.py" (
    echo ❌ Error: manage.py not found. Please run this script from the project root directory.
    pause
    exit /b 1
)

echo 🔍 Running system checks...
python manage.py check
if errorlevel 1 (
    echo ❌ System checks failed!
    pause
    exit /b 1
)

echo 🗄️ Running migrations...
python manage.py migrate
if errorlevel 1 (
    echo ❌ Migrations failed!
    pause
    exit /b 1
)

echo 🚀 Starting development server...
echo 📱 Open your browser to: http://127.0.0.1:8000
echo 🛑 Press Ctrl+C to stop the server
echo ============================================================

python manage.py runserver
pause
