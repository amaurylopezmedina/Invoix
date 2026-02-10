# Script simplificado para compilar
# Uso: .\build_simple.ps1

Write-Host "Instalando PyInstaller si es necesario..." -ForegroundColor Yellow
python -m pip install pyinstaller --quiet

Write-Host "Limpiando builds anteriores..." -ForegroundColor Yellow
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue "build", "dist", "*.spec"

Write-Host "Compilando ImportarDGII..." -ForegroundColor Cyan
Write-Host ""

# Comando PyInstaller con hidden imports para pyodbc y openpyxl
python -m PyInstaller `
    --name=ImportarDGII `
    --onefile `
    --noconsole `
    --add-data="config;config" `
    --hidden-import=pyodbc `
    --hidden-import=openpyxl `
    --hidden-import=openpyxl.cell `
    --hidden-import=openpyxl.styles `
    --hidden-import=openpyxl.chart `
    --hidden-import=openpyxl.formula `
    --hidden-import=sqlalchemy.dialects.mssql.pyodbc `
    main.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "¡Compilación exitosa!" -ForegroundColor Green
    Write-Host "Ejecutable: dist\ImportarDGII.exe" -ForegroundColor Cyan
    Start-Process "dist"
} else {
    Write-Host "Error en compilación" -ForegroundColor Red
}
