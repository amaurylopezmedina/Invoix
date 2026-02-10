# Sistema NCF - Guía de Construcción y Distribución

## 📋 Información del Proyecto
- **Nombre**: Sistema NCF Optimizado
- **Versión**: 2.0.0
- **Fecha**: 23 de enero de 2026
- **Autor**: [Tu Nombre]

## 🏗️ Construcción del Ejecutable

### Prerrequisitos
- Python 3.8+
- PyInstaller instalado: `pip install pyinstaller`
- Todas las dependencias del proyecto instaladas

### Comando de Construcción Rápido
```bash
python build_app.py
```

### Construcción Manual
```bash
# Limpiar builds anteriores
python build_app.py

# O construir manualmente
pyinstaller --clean --noconfirm app3.spec
```

## 📦 Optimizaciones Aplicadas

### 1. Librerías Incluidas (Solo las Necesarias)
- **customtkinter**: Framework de UI
- **pandas**: Procesamiento de datos
- **pyodbc**: Conexión a SQL Server
- Librerías estándar de Python

### 2. Librerías Excluidas (Para Reducir Tamaño)
- matplotlib, numpy.testing, pandas.tests
- PIL.ImageQt, PIL.ImageTk
- tkinter.test, unittest, test, pdb, pydoc

### 3. Optimizaciones de Rendimiento
- `optimize=1`: Optimización de bytecode Python
- `strip=True`: Eliminación de símbolos de debug
- `upx=True`: Compresión UPX para reducir tamaño
- `noarchive=False`: Archivado eficiente

### 4. Configuración de Producción
- `debug=False`: Sin modo debug
- `console=False`: Sin consola visible
- `disable_windowed_traceback=False`: Manejo de errores en ventana

## 📁 Estructura de Distribución

```
dist/
├── app3.exe                    # Ejecutable principal
└── [otros archivos generados]

app3_portable/
├── app3.exe                    # Ejecutable portable
├── config.ini                  # Configuración (si existe)
├── app3.log                    # Archivo de logs
└── README.md                   # Documentación portable
```

## 🚀 Despliegue

### Versión Portable
1. Extraer `app3_v2.0.0_portable.zip`
2. Configurar `config.ini` con datos de BD
3. Ejecutar `app3.exe`

### Requisitos del Sistema
- **SO**: Windows 10/11
- **Arquitectura**: x64
- **Memoria**: 4GB RAM mínimo, 8GB recomendado
- **Almacenamiento**: 200MB libres
- **Base de Datos**: SQL Server con acceso remoto

## 🔧 Configuración

### Archivo config.ini
```ini
[DATABASE]
server = TU_SERVIDOR_SQL
database = TU_BASE_DATOS
trusted_connection = no
username = TU_USUARIO
password = TU_CONTRASEÑA
port = 1433
```

### Variables de Entorno (Opcionales)
```bash
# Para conexiones específicas
set PYODBC_DRIVER=ODBC Driver 17 for SQL Server
```

## 📊 Tamaño Esperado
- **Ejecutable**: ~35-50MB (comprimido con UPX)
- **Versión portable**: ~40-60MB (incluyendo configuración)

## 🐛 Solución de Problemas

### Error de Importación
Si faltan módulos, agregar a `hiddenimports` en `app3.spec`:
```python
hiddenimports = [
    # Agregar módulos faltantes aquí
    'nombre_del_modulo',
]
```

### Error de Conexión a BD
1. Verificar configuración en `config.ini`
2. Instalar drivers ODBC de SQL Server
3. Verificar conectividad de red

### Ejecutable Muy Grande
1. Revisar `excludes` en `app3.spec`
2. Verificar que UPX esté funcionando
3. Considerar usar `--onedir` en lugar de `--onefile`

## 📈 Mejoras Futuras
- [ ] Agregar ícono personalizado
- [ ] Implementar auto-actualizaciones
- [ ] Crear instalador MSI
- [ ] Optimizar aún más excluyendo más librerías
- [ ] Agregar compresión LZMA

## 📞 Soporte
Para soporte técnico, revisar los logs en `app3.log` y verificar la configuración de base de datos.