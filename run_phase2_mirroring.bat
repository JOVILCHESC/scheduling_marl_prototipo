@echo off
REM ========================================
REM Script para ejecutar Fase 2 (Mirroring)
REM JADE refleja estado de SimPy (sin CNP)
REM ========================================

echo ========================================
echo FASE 2 - Mirroring con JADE
echo ========================================
echo.
echo NOTA: Esta fase requiere cambiar MainJADE.USE_CNP = false
echo       Actualmente el pom.xml usa MainJADEPhase3 (CNP)
echo.
echo Para ejecutar Fase 2, necesitas:
echo   1. Cambiar pom.xml mainClass a: tt.twin_scheduler.MainJADE
echo   2. Asegurar que MainJADE.USE_CNP = false
echo   3. Recompilar: mvn clean compile
echo.
echo O simplemente usa Fase 3 que incluye toda la funcionalidad.
echo.
pause
exit /b 0

REM ========================================
REM Si quieres habilitar Fase 2, descomenta:
REM ========================================
REM echo [1/4] Activando entorno virtual Python...
REM call .venv\Scripts\activate.bat
REM if %ERRORLEVEL% NEQ 0 (
REM     echo ERROR: No se pudo activar entorno virtual
REM     pause
REM     exit /b 1
REM )
REM echo     OK - Virtual environment activado
REM echo.
REM 
REM echo [2/4] Compilando código Java...
REM cd tt_twin_scheduler_2025
REM call mvn clean compile -q
REM if %ERRORLEVEL% NEQ 0 (
REM     echo ERROR: Compilacion Java fallida
REM     cd ..
REM     pause
REM     exit /b 1
REM )
REM cd ..
REM echo     OK - Codigo Java compilado
REM echo.
REM 
REM echo [3/4] Iniciando JADE (Mirroring)...
REM cd tt_twin_scheduler_2025
REM start "JADE Mirroring" cmd /k "mvn exec:java -Dexec.cleanupDaemonThreads=false -q"
REM cd ..
REM echo     OK - JADE iniciado en ventana separada
REM timeout /t 5 /nobreak >nul
REM echo.
REM 
REM echo [4/4] Ejecutando simulador con mirroring...
REM cd twin_scheduler_simpy
REM python simulator_dynamic.py --mode phase2 --duration 1000
REM cd ..
REM echo.
REM echo COMPLETADO!
REM pause
