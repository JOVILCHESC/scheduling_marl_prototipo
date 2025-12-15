@echo off
REM Script para ejecutar Fase 1 con las 3 reglas de despacho
REM No requiere JADE (usa --no-mirror)

echo ===================================
echo FASE 1: COMPARACION DE REGLAS
echo ===================================
echo.

REM Activar entorno virtual
call .venv\Scripts\activate.bat
echo.

echo [1/3] Ejecutando SPT...
python twin_scheduler_simpy/simulator_dynamic.py --mode phase1 --rule SPT --no-mirror --duration 1000
echo.

echo [2/3] Ejecutando EDD...
python twin_scheduler_simpy/simulator_dynamic.py --mode phase1 --rule EDD --no-mirror --duration 1000
echo.

echo [3/3] Ejecutando LPT...
python twin_scheduler_simpy/simulator_dynamic.py --mode phase1 --rule LPT --no-mirror --duration 1000
echo.

echo ===================================
echo COMPLETADO! Revisa la carpeta logs/
echo ===================================
pause
