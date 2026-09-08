@echo off
title OptiSchedule UMB - Iniciando Sistema...
cd /d "%~dp0"

echo ===============================================================================
echo                OPTISCHEDULE UMB - UNIVERSIDAD MANUELA BELTRAN
echo       Sistema Inteligente de Optimizacion y Asignacion de Horarios
echo ===============================================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] No se encontro el entorno virtual en .venv.
    echo Creando entorno virtual e instalando dependencias...
    python -m venv .venv
    .\.venv\Scripts\python.exe -m pip install --upgrade pip
    .\.venv\Scripts\pip.exe install -r requirements.txt
)

echo [OK] Iniciando OptiSchedule UMB con el entorno virtual del proyecto...
echo.
.\.venv\Scripts\python.exe main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [AVISO] El programa se cerro con codigo de error %ERRORLEVEL%.
    pause
)
