@echo off
title Telegram AI Reminder Bot
color 0A
echo ========================================
echo   TELEGRAM AI REMINDER BOT
echo ========================================
echo.

REM Kiểm tra Python có cài không
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python chua duoc cai dat!
    echo Vui long cai Python tu https://python.org
    pause
    exit /b 1
)

REM Kiểm tra file .env
if not exist .env (
    echo [WARNING] File .env chua ton tai!
    echo Dang sao chep tu .env.example...
    copy .env.example .env
    echo.
    echo [INFO] Vui long chinh sua file .env va them:
    echo   - TELEGRAM_BOT_TOKEN
    echo   - GEMINI_API_KEY (optional)
    echo.
    pause
    exit /b 1
)

echo [INFO] Dang khoi dong bot...
echo.

REM Chạy bot
python app.py

echo.
echo ========================================
echo Bot da dung.
echo ========================================
pause
