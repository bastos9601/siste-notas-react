@echo off
setlocal
REM Inicia el servidor y abre el navegador
set EXE_DIR=%~dp0
set EXE_PATH=%EXE_DIR%SistemaNotas.exe

if not exist "%EXE_DIR%data" mkdir "%EXE_DIR%data"
if not exist "%EXE_DIR%uploads\logos" mkdir "%EXE_DIR%uploads\logos"

start "Sistema de Notas" "%EXE_PATH%"
timeout /t 2 >nul
start "Navegador" "http://localhost:8000/"
endlocal