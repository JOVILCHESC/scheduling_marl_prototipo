@echo off
REM ========================================
REM Script para ejecutar Fase 3 (CNP)
REM Contract Net Protocol - Negociación Distribuida
REM ========================================

echo ========================================
echo FASE 3 - Contract Net Protocol (CNP)
echo ========================================
echo.

REM 1. Activar entorno virtual Python
echo [1/4] Activando entorno virtual Python...
call .venv\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: No se pudo activar entorno virtual
    pause
    exit /b 1
)
echo     OK - Virtual environment activado
echo.

REM 2. Compilar código Java (si es necesario)
echo [2/4] Compilando código Java Phase 3...
cd tt_twin_scheduler_2025
call mvn clean compile -q
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Compilacion Java fallida
    cd ..
    pause
    exit /b 1
)
cd ..
echo     OK - Codigo Java compilado
echo.

REM 3. Iniciar JADE Phase 3 en background
echo [3/4] Iniciando JADE Phase 3 (CNP)...
cd tt_twin_scheduler_2025
start "JADE Phase 3" cmd /k "mvn exec:java -Dexec.cleanupDaemonThreads=false -q"
cd ..
echo     OK - JADE Phase 3 iniciado en ventana separada
echo     Esperando 5 segundos para que JADE inicie completamente...
timeout /t 5 /nobreak >nul
echo.

REM 4. Ejecutar simulador Phase 3 CNP
echo [4/4] Ejecutando simulador Phase 3 (CNP)...
echo     Parametros: duration=1000, arrival_rate=0.4, mtbf=100, mttr=8
echo.
python -m twin_scheduler_simpy.simulator_phase3_cnp --duration 1000 --arrival-rate 0.4 --mtbf 100 --mttr 8 --seed 42

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Simulacion fallida
    pause
    exit /b 1
)

echo.
echo ========================================
echo FASE 3 COMPLETADA
echo ========================================
echo.
echo Resultados en: logs\simulation_phase3_cnp_*.csv
echo.
echo NOTA: Cierra manualmente la ventana de JADE cuando termines
echo.
pause
