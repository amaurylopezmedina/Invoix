@echo off
setlocal ENABLEDELAYEDEXPANSION
title Compilacion Profesional — PyArmor 8 + Nuitka
color 0B

:: =================================================================
:: ARCHIVOS A COMPILAR
:: =================================================================
set FILE1=FEGeneraryFirmaXMLASESYS.py
set FILE2=FEEnvioASESYS.py
set FILE3=FEConsultaEstadoECF.py
set FILE4=FEImpresionASESYS.py
set FILE5=ipre.py

:: =================================================================
:: CONFIGURACION
:: =================================================================
set BUILD_DIR=build
set DIST_DIR=dist
set LOG_DIR=logs

echo ==============================================================
echo COMPILACION PROFESIONAL — PyArmor 8 + Nuitka
echo CON HISTORIAL COMPLETO EN CONSOLA
echo ==============================================================

mkdir %BUILD_DIR% >nul 2>&1
mkdir %DIST_DIR% >nul 2>&1
mkdir %LOG_DIR% >nul 2>&1

:: =================================================================
:: VERIFICACIONES
:: =================================================================
call :Check "PyArmor"  "pyarmor --version"
call :Check "Nuitka"   "python -m nuitka --version"
call :Check "Compilador"  "cl.exe"

:: =================================================================
:: PROCESAR ARCHIVOS
:: =================================================================
call :COMPILAR "%FILE1%"
call :COMPILPAR "%FILE2%"
call :COMPILAR "%FILE3%"
call :COMPILAR "%FILE4%"
call :COMPILAR "%FILE5%"

echo ==============================================================
echo EJECUTABLES LISTOS EN: %DIST_DIR%
echo Logs en: %LOG_DIR%
echo ==============================================================
pause
exit /b


:: =================================================================
:: SUBRUTINA DE COMPILACION
:: =================================================================
:COMPILAR
set FILE=%~1
set NAME=%~n1
set LOGFILE=%LOG_DIR%\%NAME%.log

echo.
echo ---------------------------------------------------------
echo COMPILANDO: %FILE%
echo ---------------------------------------------------------
echo Iniciando... > %LOGFILE%

rmdir /s /q %BUILD_DIR%\%NAME% >nul 2>&1
mkdir %BUILD_DIR%\%NAME%

:: ========================
:: PROGRESO (SIN BORRAR PANTALLA)
:: ========================
echo [++++++++++++] 25%%  Ofuscando con PyArmor...

pyarmor gen --output %BUILD_DIR%\%NAME% %FILE% >> %LOGFILE% 2>&1
if %errorlevel% neq 0 (
    echo ERROR en PyArmor: %FILE%
    exit /b
)

echo [++++++++++++++++++++++++++++] 75%%  Compilando con Nuitka...

python -m nuitka ^
  --onefile ^
  --standalone ^
  --follow-imports ^
  --output-dir=%DIST_DIR% ^
  %BUILD_DIR%\%NAME%\%NAME%.py

if %errorlevel% neq 0 (
    echo ERROR compilando %FILE% con Nuitka
    exit /b
)

echo [++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++] 100%% Finalizado

echo COMPILADO: %FILE%
echo.
exit /b


:: =================================================================
:: SUBRUTINA DE VERIFICACION
:: =================================================================
:Check
set NAME=%~1
set CMD=%~2

echo Verificando %NAME%...
%CMD% >nul 2>&1
if %errorlevel% neq 0 (
    echo %NAME% NO ENCONTRADO.
    pause
    exit /b
)
echo %NAME% OK
exit /b
