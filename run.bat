@echo off
title OptiSchedule UMB - Iniciando Sistema...
cd /d "%~dp0"

echo ===============================================================================
echo                OPTISCHEDULE UMB - UNIVERSIDAD MANUELA BELTRAN
echo       Sistema Inteligente de Optimizacion y Asignacion de Horarios
echo ===============================================================================
echo.

if exist ".venv\Scripts\python.exe" (
    echo [OK] Iniciando OptiSchedule UMB con entorno virtual .venv...
    .\.venv\Scripts\python.exe main.py
) else (
    echo [OK] Iniciando OptiSchedule UMB con Python del sistema...
    python main.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [AVISO] El programa se cerro con codigo de error %ERRORLEVEL%.
    pause
)
