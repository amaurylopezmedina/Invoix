# Instrucciones para compilar ImportarDGII a .exe

## Método 1: Script Automático (Recomendado)

Ejecuta en PowerShell:
```powershell
.\build_simple.ps1
```

O si quieres la versión completa con icono:
```powershell
.\build_exe.ps1
```

## Método 2: Manual

1. Instalar PyInstaller:
```powershell
pip install pyinstaller
```

2. Compilar:
```powershell
pyinstaller --name=ImportarDGII --onefile --noconsole --add-data="config;config" main.py
```

3. El ejecutable estará en: `dist\ImportarDGII.exe`

## Distribución

Para distribuir la aplicación, necesitas copiar:
- `dist\ImportarDGII.exe` (el ejecutable)
- Carpeta `config\` (con los archivos JSON)

**Nota:** El usuario final necesita tener instalado:
- ODBC Driver 17 for SQL Server (o el driver que uses)
- Microsoft Visual C++ Redistributable

## Solución de Problemas

Si el ejecutable no inicia:
1. Ejecuta desde CMD/PowerShell para ver errores: `.\ImportarDGII.exe`
2. Verifica que la carpeta `config` esté junto al .exe
3. Compila sin `--noconsole` para ver mensajes de error

Si hay errores de imports:
```powershell
pyinstaller --hidden-import=pandas --hidden-import=openpyxl --hidden-import=sqlalchemy --hidden-import=pyodbc --onefile main.py
```

## Tamaño del Ejecutable

El ejecutable será de aproximadamente 80-150 MB debido a las dependencias:
- PyQt6 (~40 MB)
- pandas + numpy (~30 MB)
- SQLAlchemy + pyodbc (~10 MB)
- Otras librerías (~10 MB)

Para reducir tamaño, considera usar `--onedir` en lugar de `--onefile`.
