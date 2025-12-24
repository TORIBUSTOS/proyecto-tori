@echo off
chcp 65001 >nul
cls

echo ================================================================================
echo 🐂 TORO Investment Manager - Sistema Web
echo ================================================================================
echo.
echo Iniciando servidor...
echo.

REM Verificar si existe el entorno virtual
if not exist ".venv\Scripts\activate.bat" (
    if not exist "venv\Scripts\activate.bat" (
        echo [ERROR] No se encuentra el entorno virtual.
        echo.
        echo Por favor, ejecuta primero:
        echo    python -m venv .venv
        echo    .venv\Scripts\activate
        echo    pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
)

REM Activar entorno virtual (probar ambas ubicaciones)
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    call venv\Scripts\activate.bat
)

echo [OK] Entorno virtual activado
echo.

REM Verificar que uvicorn esté instalado
python -c "import uvicorn" 2>nul
if errorlevel 1 (
    echo [ERROR] uvicorn no está instalado.
    echo.
    echo Instalando dependencias...
    pip install -r requirements.txt
    echo.
)

echo ================================================================================
echo Iniciando servidor FastAPI en http://localhost:8000
echo ================================================================================
echo.
echo Accesos disponibles:
echo   - Dashboard:     http://localhost:8000
echo   - Reportes:      http://localhost:8000/reportes
echo   - Batches:       http://localhost:8000/batches
echo   - API Docs:      http://localhost:8000/docs
echo.
echo Presiona Ctrl+C para detener el servidor
echo ================================================================================
echo.

REM Esperar 2 segundos antes de abrir el navegador
timeout /t 2 /nobreak >nul

REM Abrir navegador en segundo plano
start http://localhost:8000

REM Iniciar servidor (bloqueante)
python run.py

REM Si el servidor se detiene, pausar para ver errores
echo.
echo ================================================================================
echo Servidor detenido
echo ================================================================================
pause
