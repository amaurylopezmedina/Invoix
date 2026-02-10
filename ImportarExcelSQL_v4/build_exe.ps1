# Script para compilar la aplicación a ejecutable .exe
# Uso: .\build_exe.ps1

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Compilador de ImportarDGII v4.0" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si PyInstaller está instalado
Write-Host "Verificando PyInstaller..." -ForegroundColor Yellow
$pyinstallerCheck = python -m pip show pyinstaller 2>$null

if (-not $pyinstallerCheck) {
    Write-Host "PyInstaller no está instalado. Instalando..." -ForegroundColor Yellow
    python -m pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error al instalar PyInstaller" -ForegroundColor Red
        exit 1
    }
    Write-Host "PyInstaller instalado correctamente" -ForegroundColor Green
} else {
    Write-Host "PyInstaller ya está instalado" -ForegroundColor Green
}

Write-Host ""
Write-Host "Limpiando builds anteriores..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "*.spec") { Remove-Item -Force "*.spec" }

Write-Host "Compilando aplicación..." -ForegroundColor Yellow
Write-Host ""

# Ejecutar PyInstaller con configuración optimizada
pyinstaller `
    --name="ImportarDGII" `
    --onefile `
    --windowed `
    --icon="icon.ico" `
    --add-data="config;config" `
    --hidden-import="PyQt6" `
    --hidden-import="PyQt6.QtCore" `
    --hidden-import="PyQt6.QtWidgets" `
    --hidden-import="PyQt6.QtGui" `
    --hidden-import="pandas" `
    --hidden-import="openpyxl" `
    --hidden-import="sqlalchemy" `
    --hidden-import="pyodbc" `
    --hidden-import="numpy" `
    --noconsole `
    main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "================================" -ForegroundColor Green
    Write-Host "Compilación exitosa!" -ForegroundColor Green
    Write-Host "================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "El ejecutable está en: dist\ImportarDGII.exe" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Tamaño del archivo:" -ForegroundColor Yellow
    $size = (Get-Item "dist\ImportarDGII.exe").Length / 1MB
    Write-Host ("{0:N2} MB" -f $size) -ForegroundColor Cyan
    Write-Host ""
    
    # Abrir carpeta dist
    Write-Host "Abriendo carpeta de distribución..." -ForegroundColor Yellow
    Start-Process "dist"
} else {
    Write-Host ""
    Write-Host "Error en la compilación" -ForegroundColor Red
    exit 1
}
