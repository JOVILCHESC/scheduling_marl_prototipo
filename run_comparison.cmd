@echo off
REM Script para ejecutar la comparación de Fase 1 vs Fase 2
REM Establece UTF-8 para evitar errores de codificación en Windows

setlocal enabledelayedexpansion
cd /d "%~dp0"

REM Establecer encoding UTF-8
set PYTHONIOENCODING=utf-8

REM Ejecutar main_comparison con argumentos
python -m twin_scheduler_simpy.main_comparison %*

endlocal
