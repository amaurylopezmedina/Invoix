# ImportarDGII - Documentación para Integración API

## Descripción General

**ImportarDGII** es un sistema para importar archivos Excel de Facturación Electrónica (FE) de la DGII hacia una base de datos SQL Server. El sistema procesa archivos Excel con estructura específica de encabezados y detalles de facturas electrónicas, validando duplicados y manteniendo la integridad de los datos.

Este documento se enfoca en los componentes核心 del sistema que pueden ser integrados en una API web, **omitiendo la interfaz gráfica (PyQt6)**.

---

## Arquitectura del Sistema

### Estructura de Directorios

```
ImportarExcelSQL_v4/
├── config/                          # Archivos de configuración
│   ├── settings.json               # Configuración de conexión DB
│   ├── encabezado_columns.json     # Definición columnas encabezado
│   └── detalle_columns.json        # Definición columnas detalle
├── core/                           # Lógica de negocio (API-ready)
│   ├── db_manager.py               # Gestión de base de datos
│   └── excel_loader.py             # Carga y limpieza de Excel
├── ui/                             # Interfaz gráfica (ignorar para API)
│   ├── main_window.py
│   └── config_window.py
├── main.py                         # Punto de entrada GUI (ignorar)
└── requirements.txt                # Dependencias Python
```

---

## Componentes Principales para API

### 1. **Módulo: `excel_loader.py`**

**Ubicación:** `core/excel_loader.py`

**Propósito:** Cargar y limpiar datos de archivos Excel.

#### Función Principal: `load_excel()`

```python
def load_excel(path_excel: str) -> pd.DataFrame:
    """
    Lee el Excel y reemplaza valores especiales con None (NULL):
    - Celdas vacías → None
    - '#e' / '#E' → None
    - 'NULL' → None
    - 'nan', 'NaN' → None
    - Espacios en blanco → None
    
    Args:
        path_excel: Ruta completa al archivo Excel (.xlsx)
    
    Returns:
        pd.DataFrame: DataFrame con datos limpios
    """
```

**Uso en API:**
```python
from core.excel_loader import load_excel

# Cargar archivo Excel subido por el usuario
df = load_excel("/path/to/uploaded/file.xlsx")
```

**Características:**
- Limpia automáticamente valores nulos/inválidos
- Convierte errores de Excel (#e, #E) a None
- Preserva tipos de datos como strings para validación posterior
- Engine: `openpyxl` para compatibilidad con .xlsx

---

### 2. **Módulo: `db_manager.py`**

**Ubicación:** `core/db_manager.py`

**Propósito:** Gestionar conexión, esquema y operaciones con SQL Server.

#### Funciones Clave para API

##### 2.1 `load_settings()` y `save_settings()`

```python
def load_settings() -> Dict[str, str]:
    """Carga configuración desde config/settings.json"""
    
def save_settings(cfg: dict) -> None:
    """Guarda configuración en config/settings.json"""
```

**Configuración requerida (`settings.json`):**
```json
{
  "server": "localhost",
  "database": "ImportarFE",
  "user": "SISTEMA",
  "password": "@@sistema",
  "table_encabezado": "FEEncabezado",
  "table_detalle_prefix": "FEDetalle",
  "driver": "ODBC Driver 17 for SQL Server",
  "validate_duplicates": true,
  "theme": "dark"
}
```

**Parámetros importantes:**
- `server`: Servidor SQL Server (IP o hostname)
- `database`: Nombre de la base de datos
- `user` / `password`: Credenciales de autenticación
- `table_encabezado`: Nombre de tabla para encabezados de facturas
- `table_detalle_prefix`: Prefijo para tabla(s) de detalles
- `driver`: Driver ODBC (típicamente "ODBC Driver 17 for SQL Server")
- `validate_duplicates`: Si `true`, evita insertar registros duplicados

---

##### 2.2 `ensure_database_exists()`

```python
def ensure_database_exists() -> None:
    """
    Crea la base de datos si no existe.
    Usa conexión AUTOCOMMIT para evitar errores.
    """
```

**Uso en API:**
```python
from core.db_manager import ensure_database_exists

# Llamar al iniciar la aplicación o endpoint
ensure_database_exists()
```

---

##### 2.3 `ensure_tables_exist()`

```python
def ensure_tables_exist(df: pd.DataFrame, recreate_mode: bool = False) -> List[str]:
    """
    Garantiza que las tablas estén listas.
    
    Args:
        df: DataFrame con los datos a importar
        recreate_mode: 
            - True: Elimina y recrea tablas (borra datos existentes)
            - False: Preserva datos existentes (modo append)
    
    Returns:
        Lista de nombres de tablas creadas/validadas
    """
```

**Modos de operación:**

1. **Modo RECREAR** (`recreate_mode=True`):
   - Elimina tablas existentes
   - Recrea con esquema JSON
   - **¡PRECAUCIÓN!** Borra todos los datos

2. **Modo AGREGAR** (`recreate_mode=False`):
   - Sincroniza esquema sin borrar datos
   - Agrega columnas faltantes
   - Ajusta tipos de datos si difieren

**Uso en API:**
```python
from core.db_manager import ensure_tables_exist

# Modo agregar (recomendado para producción)
ensure_tables_exist(df, recreate_mode=False)

# Modo recrear (solo para desarrollo/testing)
ensure_tables_exist(df, recreate_mode=True)
```

---

##### 2.4 `split_dataframe()`

```python
def split_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
    """
    Divide el DataFrame Excel en:
    1. Encabezado (df_head): Columnas definidas en encabezado_columns.json
    2. Detalle (det_tables): Columnas indexadas [1], [2], [3]... transpuestas a filas
    
    Returns:
        Tuple[pd.DataFrame, Dict[str, pd.DataFrame]]:
            - df_head: DataFrame de encabezados
            - det_tables: Diccionario {'FEDetalle': df_detalle}
    """
```

**Comportamiento:**
- **Filtrado por JSON**: Solo procesa columnas definidas en archivos JSON
- **Transposición de detalles**: Convierte columnas horizontales `Campo[1]`, `Campo[2]`... en filas verticales
- **Validación de datos**: Filtra ítems sin `CantidadItem` válida
- **Normalización**: Remueve corchetes de nombres (`FormaPago[1]` → `FormaPago1`)

**Ejemplo de transformación:**

**Excel original (horizontal):**
| eNCF | RNCEmisor | NumeroLinea[1] | CantidadItem[1] | NumeroLinea[2] | CantidadItem[2] |
|------|-----------|----------------|-----------------|----------------|-----------------|
| E001 | 123456789 | 1              | 10              | 2              | 5               |

**Detalle transpuesto (vertical):**
| eNCF | RNCEmisor | NumeroLinea | CantidadItem |
|------|-----------|-------------|--------------|
| E001 | 123456789 | 1           | 10           |
| E001 | 123456789 | 2           | 5            |

---

##### 2.5 `insert_dataframes()`

```python
def insert_dataframes(
    df_head: pd.DataFrame, 
    det_tables: Dict[str, pd.DataFrame]
) -> Tuple[int, Dict[str, int]]:
    """
    Inserta encabezados y detalles en SQL Server.
    
    Args:
        df_head: DataFrame de encabezados
        det_tables: Diccionario de DataFrames de detalles
    
    Returns:
        Tuple[int, Dict[str, int]]:
            - Número de encabezados insertados
            - Diccionario con filas insertadas por tabla de detalle
    """
```

**Características:**
- **Validación de duplicados**: Si `validate_duplicates=true`, verifica `ENCF` + `RNCEmisor`
- **Modo append**: Siempre agrega datos, nunca reemplaza
- **Conversión automática de tipos**:
  - INT: `TipoECF`, `TipoPago`, etc.
  - BIT (booleano): `IndicadorNotaCredito`, etc.
  - DATE: `FechaEmision`, `FechaEntrega`, etc.
  - DECIMAL: Montos, cantidades, precios
- **Columnas automáticas**: Agrega `fechacreacion` y `Modificado` con timestamp actual

**Uso en API:**
```python
from core.db_manager import insert_dataframes

head_count, detail_counts = insert_dataframes(df_head, det_tables)
print(f"Insertados: {head_count} encabezados, {sum(detail_counts.values())} detalles")
```

---

##### 2.6 `test_connection()`

```python
def test_connection() -> Tuple[bool, str]:
    """
    Prueba la conexión a SQL Server.
    
    Returns:
        Tuple[bool, str]: (éxito, mensaje de error si falló)
    """
```

**Uso en API:**
```python
from core.db_manager import test_connection

success, error_msg = test_connection()
if not success:
    return {"error": f"Conexión fallida: {error_msg}"}, 500
```

---

### 3. **Archivos de Configuración JSON**

#### 3.1 `config/settings.json`

Configuración de conexión y comportamiento del sistema.

```json
{
  "server": "localhost",
  "database": "ImportarFE",
  "user": "SISTEMA",
  "password": "@@sistema",
  "table_encabezado": "FEEncabezado",
  "table_detalle_prefix": "FEDetalle",
  "driver": "ODBC Driver 17 for SQL Server",
  "validate_duplicates": true,
  "theme": "dark"
}
```

**Parámetros configurables:**
- Conexión DB: `server`, `database`, `user`, `password`, `driver`
- Nombres de tablas: `table_encabezado`, `table_detalle_prefix`
- Comportamiento: `validate_duplicates` (evitar duplicados)
- UI: `theme` (ignorar en API)

---

#### 3.2 `config/encabezado_columns.json`

Define el esquema de la tabla de encabezados.

**Estructura:**
```json
{
  "NombreColumna": {
    "type": "NVARCHAR | DECIMAL | DATE | INT | BIT",
    "length": 100,          // Solo para NVARCHAR
    "precision": 18,        // Solo para DECIMAL
    "scale": 4,             // Solo para DECIMAL
    "nullable": true,
    "description": "Descripción del campo"
  }
}
```

**Ejemplo:**
```json
{
  "TipoECF": {
    "type": "NVARCHAR",
    "length": 100,
    "nullable": true,
    "description": "Tipo de comprobante fiscal electrónico"
  },
  "eNCF": {
    "type": "NVARCHAR",
    "length": 100,
    "nullable": true,
    "description": "Número de comprobante fiscal electrónico"
  },
  "FechaEmision": {
    "type": "NVARCHAR",
    "length": 100,
    "nullable": true,
    "description": "Fecha de emisión de la factura"
  },
  "MontoTotal": {
    "type": "DECIMAL",
    "precision": 18,
    "scale": 4,
    "nullable": true,
    "description": "Monto total de la factura"
  }
}
```

**Columnas críticas (Primary Key):**
- `ENCF`: Número de comprobante fiscal (parte de PK compuesta)
- `RNCEmisor`: RNC del emisor (parte de PK compuesta)

---

#### 3.3 `config/detalle_columns.json`

Define el esquema de la tabla de detalles (ítems de facturas).

**Estructura:** Igual que `encabezado_columns.json`

**Ejemplo:**
```json
{
  "NumeroLinea": {
    "type": "NVARCHAR",
    "length": 100,
    "nullable": true,
    "description": "Número de línea del ítem"
  },
  "TipoCodigo1": {
    "type": "NVARCHAR",
    "length": 100,
    "nullable": true,
    "description": "Tipo de código del ítem [1]"
  },
  "CodigoItem1": {
    "type": "NVARCHAR",
    "length": 100,
    "nullable": true,
    "description": "Código del ítem [1]"
  },
  "CantidadItem": {
    "type": "NVARCHAR",
    "length": 100,
    "nullable": true,
    "description": "Cantidad del ítem"
  },
  "PrecioUnitarioItem": {
    "type": "DECIMAL",
    "precision": 18,
    "scale": 4,
    "nullable": true,
    "description": "Precio unitario del ítem"
  }
}
```

**Columnas indexadas:**
- Campos como `TipoCodigo[1]`, `TipoCodigo[2]`, `TipoCodigo[3]` se definen sin índice en JSON
- El sistema detecta automáticamente los índices `[1]`, `[2]`, `[3]`... en el Excel
- Los transpone a filas separadas con `NumeroLinea` como identificador

---

## Flujo de Trabajo Completo para API

### Flujo Recomendado

```python
from core.excel_loader import load_excel
from core.db_manager import (
    ensure_database_exists,
    ensure_tables_exist,
    split_dataframe,
    insert_dataframes,
    test_connection
)

# 1. Validar conexión
success, error = test_connection()
if not success:
    raise Exception(f"Error de conexión: {error}")

# 2. Asegurar que la BD existe
ensure_database_exists()

# 3. Cargar Excel
df = load_excel("/ruta/archivo.xlsx")

# 4. Crear/validar tablas (modo append recomendado)
ensure_tables_exist(df, recreate_mode=False)

# 5. Dividir en encabezado y detalle
df_head, det_tables = split_dataframe(df)

# 6. Insertar en base de datos
head_count, detail_counts = insert_dataframes(df_head, det_tables)

# 7. Respuesta
response = {
    "success": True,
    "encabezados_insertados": head_count,
    "detalles_insertados": sum(detail_counts.values()),
    "tablas_detalle": detail_counts
}
```

---

## Ejemplo de Endpoint FastAPI

```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import tempfile
import os
from pathlib import Path

# Importar módulos del sistema
from core.excel_loader import load_excel
from core.db_manager import (
    ensure_database_exists,
    ensure_tables_exist,
    split_dataframe,
    insert_dataframes,
    test_connection
)

app = FastAPI(title="ImportarDGII API")

@app.post("/api/importar-excel")
async def importar_excel(
    file: UploadFile = File(...),
    recreate: bool = False  # Query param: ?recreate=true
):
    """
    Importa un archivo Excel de facturas DGII a SQL Server.
    
    Args:
        file: Archivo Excel (.xlsx)
        recreate: Si true, recrea tablas (¡borra datos existentes!)
    
    Returns:
        JSON con resultados de la importación
    """
    
    # Validar tipo de archivo
    if not file.filename.endswith('.xlsx'):
        raise HTTPException(
            status_code=400, 
            detail="Solo se permiten archivos .xlsx"
        )
    
    # Guardar archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # 1. Validar conexión
        success, error = test_connection()
        if not success:
            raise HTTPException(
                status_code=500,
                detail=f"Error de conexión a DB: {error}"
            )
        
        # 2. Asegurar BD existe
        ensure_database_exists()
        
        # 3. Cargar Excel
        df = load_excel(tmp_path)
        
        if len(df) == 0:
            raise HTTPException(
                status_code=400,
                detail="El archivo Excel está vacío"
            )
        
        # 4. Crear/validar tablas
        ensure_tables_exist(df, recreate_mode=recreate)
        
        # 5. Dividir datos
        df_head, det_tables = split_dataframe(df)
        
        if len(df_head) == 0:
            raise HTTPException(
                status_code=400,
                detail="No se encontraron encabezados válidos"
            )
        
        # 6. Insertar datos
        head_count, detail_counts = insert_dataframes(df_head, det_tables)
        
        # 7. Respuesta exitosa
        return JSONResponse(content={
            "success": True,
            "mensaje": "Importación completada exitosamente",
            "resultados": {
                "encabezados_insertados": head_count,
                "detalles_insertados": sum(detail_counts.values()),
                "tablas_detalle": detail_counts
            },
            "archivo": file.filename
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar archivo: {str(e)}"
        )
    finally:
        # Limpiar archivo temporal
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.get("/api/health")
async def health_check():
    """Verifica estado de conexión a BD"""
    success, error = test_connection()
    
    if success:
        return {"status": "healthy", "database": "connected"}
    else:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": error}
        )


@app.get("/api/config")
async def get_config():
    """Obtiene configuración actual (sin password)"""
    from core.db_manager import load_settings
    
    cfg = load_settings()
    # Ocultar password
    safe_cfg = {k: v for k, v in cfg.items() if k != 'password'}
    
    return safe_cfg
```

---

## Requisitos del Sistema

### Dependencias Python

**Archivo:** `requirements.txt`

```
pandas>=2.0.0
openpyxl>=3.1.0
SQLAlchemy>=2.0.0
pyodbc>=5.0.0
# PyQt6>=6.5.0  # No necesario para API
```

**Instalación:**
```bash
pip install pandas openpyxl SQLAlchemy pyodbc
```

**Dependencias adicionales para API:**
```bash
# FastAPI
pip install fastapi uvicorn[standard] python-multipart

# Flask (alternativa)
pip install flask flask-cors
```

---

### Requisitos de SQL Server

1. **Versión:** SQL Server 2016 o superior
2. **Driver ODBC:** 
   - Windows: "ODBC Driver 17 for SQL Server"
   - Linux: "ODBC Driver 18 for SQL Server"
3. **Permisos de usuario:**
   - `CREATE DATABASE` (para crear BD si no existe)
   - `CREATE TABLE` (para crear tablas)
   - `INSERT`, `SELECT` (para operaciones CRUD)
4. **Autenticación:** SQL Server Authentication (usuario/password)

**Instalación driver ODBC:**

**Windows:**
```powershell
# Descargar desde Microsoft
https://docs.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server
```

**Linux:**
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

---

## Validaciones y Reglas de Negocio

### 1. **Validación de Duplicados**

**Configuración:** `settings.json` → `"validate_duplicates": true`

**Comportamiento:**
- Verifica combinación única de `ENCF` + `RNCEmisor`
- Si existe registro con misma combinación, lo omite
- Previene insertar facturas duplicadas

**Desactivar:**
```json
{
  "validate_duplicates": false
}
```

---

### 2. **Limpieza de Datos**

**Valores convertidos a NULL:**
- Celdas vacías
- `#e`, `#E` (errores de Excel)
- `NULL`, `null` (texto)
- `NaN`, `nan`
- Strings con solo espacios

**Ejemplo:**
```python
# Antes
"  #e  " → None
"NULL"   → None
""       → None
"123"    → "123"

# Después de limpieza
None
None
None
"123"
```

---

### 3. **Conversión de Tipos**

**Encabezado:**
- **INT:** `TipoECF`, `TipoPago`
- **BIT (booleano):** `IndicadorNotaCredito`, `IndicadorEnvioDiferido`
- **DATE:** `FechaEmision`, `FechaVencimientoSecuencia`, `FechaLimitePago`
- **DATETIME:** `fechacreacion`, `Modificado` (automáticas)

**Detalle:**
- **INT:** `NumeroLinea`, `TipoECF`, `IndicadorFacturacion`
- **DECIMAL:** `CantidadItem`, `PrecioUnitarioItem`, `MontoItem`, `MontoITBISRetenido`
- **DATE:** `FechaElaboracion`, `FechaVencimientoItem`

---

### 4. **Filtrado de Ítems de Detalle**

**Regla:** Solo se insertan ítems con `CantidadItem` válida (no NULL, no vacío)

**Ejemplo:**
```
Factura E001 tiene 3 ítems en Excel:
- Item [1]: CantidadItem = 10    → Se inserta
- Item [2]: CantidadItem = NULL  → Se omite
- Item [3]: CantidadItem = 5     → Se inserta

Resultado: 2 filas en tabla FEDetalle
```

---

## Estructura de Base de Datos

### Tabla: `FEEncabezado` (Encabezados de Facturas)

**Primary Key:** Compuesta `(ENCF, RNCEmisor)`

**Columnas principales:**
```sql
CREATE TABLE FEEncabezado (
    ENCF NVARCHAR(100) NOT NULL,          -- Número de comprobante
    RNCEmisor NVARCHAR(100) NOT NULL,     -- RNC del emisor
    TipoECF INT NULL,                     -- Tipo de comprobante
    eNCF NVARCHAR(100) NULL,              -- NCF electrónico
    FechaEmision DATE NULL,               -- Fecha de emisión
    MontoTotal DECIMAL(18,4) NULL,        -- Monto total
    IndicadorNotaCredito BIT NULL,        -- Es nota de crédito
    fechacreacion DATETIME NOT NULL,      -- Timestamp creación
    Modificado DATETIME NOT NULL,         -- Timestamp modificación
    -- ... más columnas según JSON
    PRIMARY KEY (ENCF, RNCEmisor)
);
```

---

### Tabla: `FEDetalle` (Ítems de Facturas)

**Foreign Key:** Referencia a `FEEncabezado` mediante `(eNCF, RNCEmisor)`

**Columnas principales:**
```sql
CREATE TABLE FEDetalle (
    eNCF NVARCHAR(100) NULL,              -- NCF electrónico (FK)
    RNCEmisor NVARCHAR(100) NULL,         -- RNC emisor (FK)
    TipoECF INT NULL,                     -- Tipo de comprobante
    NumeroLinea INT NULL,                 -- Número de ítem
    CantidadItem DECIMAL(18,4) NULL,      -- Cantidad
    PrecioUnitarioItem DECIMAL(18,4) NULL,-- Precio unitario
    MontoItem DECIMAL(18,4) NULL,         -- Monto del ítem
    DescripcionItem NVARCHAR(500) NULL,   -- Descripción
    -- ... más columnas según JSON
);
```

**Nota:** No tiene PK definida, pero típicamente se usa combinación `(eNCF, RNCEmisor, NumeroLinea)` como identificador único.

---

## Manejo de Errores

### Errores Comunes y Soluciones

#### 1. **Error de Conexión a SQL Server**

**Error:**
```
Error de conexión: [08001] [Microsoft][ODBC Driver 17 for SQL Server]
```

**Soluciones:**
- Verificar `server` en `settings.json` (IP/hostname correcto)
- Verificar que SQL Server esté iniciado
- Verificar firewall (puerto 1433 abierto)
- Verificar credenciales `user` y `password`
- Verificar que el driver ODBC esté instalado

---

#### 2. **Error: "Database does not exist"**

**Error:**
```
Cannot open database "ImportarFE" requested by the login
```

**Solución:**
```python
# Llamar antes de cualquier operación
ensure_database_exists()
```

---

#### 3. **Error: "Invalid column name"**

**Error:**
```
Invalid column name 'FormaPago[1]'
```

**Causa:** Nombres de columnas con corchetes no están siendo normalizados

**Solución:** 
- Asegurar que `split_dataframe()` normaliza nombres
- Verificar que `encabezado_columns.json` tenga la columna definida
- Usar `_normalize_column_names()` internamente

---

#### 4. **Error: "Cannot insert NULL into column"**

**Error:**
```
Cannot insert the value NULL into column 'fechacreacion'
```

**Causa:** Columnas NOT NULL sin valor por defecto

**Solución:**
- `fechacreacion` y `Modificado` se agregan automáticamente con timestamp
- Verificar que `insert_dataframes()` esté agregando estas columnas

---

#### 5. **Error: "Duplicate key"**

**Error:**
```
Violation of PRIMARY KEY constraint 'PK_FEEncabezado'. 
Cannot insert duplicate key in object 'dbo.FEEncabezado'. 
The duplicate key value is (E001, 123456789).
```

**Causa:** Intentar insertar registro con `ENCF` + `RNCEmisor` existente

**Solución:**
- Habilitar validación: `"validate_duplicates": true` en `settings.json`
- El sistema omitirá automáticamente duplicados
- Revisar logs para ver registros omitidos

---

## Logs y Debugging

### Función: `safe_print()`

```python
def safe_print(msg: str) -> None:
    """
    Imprime mensajes protegiendo contra errores de codificación.
    Reemplaza emojis con códigos ASCII en Windows.
    """
```

**Emojis usados:**
- 🗑️ `[DEL]` - Eliminando tabla
- ✅ `[OK]` - Operación exitosa
- ⚠️ `[WARN]` - Advertencia
- 💥 `[ERROR]` - Error crítico
- 🔍 `[INFO]` - Información
- ⚙️ `[PROC]` - Procesando
- ➕ `[ADD]` - Agregando columna

**Ejemplos de logs:**
```
📋 Columnas válidas de encabezado en JSON: 145
📊 Transponiendo 240 columnas de detalle a formato vertical...
✅ Detalle transpuesto: 1250 filas con CantidadItem válida (150 filas sin cantidad eliminadas)
🔍 Validando duplicados antes de insertar...
⚠️ Se encontraron 5 registros duplicados que serán omitidos
✅ Se insertarán 95 registros nuevos
✅ Encabezado: 95 filas insertadas (agregadas a tabla existente).
```

---

## Configuración de Columnas Adicionales

### Agregar Nueva Columna de Encabezado

1. **Editar:** `config/encabezado_columns.json`

```json
{
  "NuevaColumna": {
    "type": "NVARCHAR",
    "length": 200,
    "nullable": true,
    "description": "Descripción de la nueva columna"
  }
}
```

2. **Ejecutar:** `ensure_tables_exist(df, recreate_mode=False)`
   - El sistema detectará la nueva columna
   - La agregará automáticamente a la tabla existente
   - Logs mostrarán: `➕ Columna agregada: NuevaColumna (NVARCHAR(200))`

---

### Agregar Nueva Columna de Detalle

1. **Editar:** `config/detalle_columns.json`

```json
{
  "NuevoCampo": {
    "type": "DECIMAL",
    "precision": 10,
    "scale": 2,
    "nullable": true,
    "description": "Nuevo campo de detalle"
  }
}
```

2. **Excel debe contener:** `NuevoCampo[1]`, `NuevoCampo[2]`, `NuevoCampo[3]`...
3. **Sistema automáticamente:**
   - Detecta índices `[1]`, `[2]`, `[3]`...
   - Transpone a filas separadas
   - Crea columna `NuevoCampo` en tabla `FEDetalle`

---

## Mejores Prácticas para Integración API

### 1. **Manejo Asíncrono**

```python
from fastapi import BackgroundTasks

@app.post("/api/importar-excel-async")
async def importar_excel_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    # Guardar archivo
    tmp_path = save_uploaded_file(file)
    
    # Procesar en background
    background_tasks.add_task(procesar_excel, tmp_path)
    
    return {"message": "Archivo en cola de procesamiento", "status": "pending"}
```

---

### 2. **Validación de Esquema**

```python
from pydantic import BaseModel

class ConfigDB(BaseModel):
    server: str
    database: str
    user: str
    password: str
    driver: str = "ODBC Driver 17 for SQL Server"
    validate_duplicates: bool = True

@app.post("/api/config/update")
async def update_config(config: ConfigDB):
    save_settings(config.dict())
    return {"message": "Configuración actualizada"}
```

---

### 3. **Rate Limiting**

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/importar-excel")
@limiter.limit("10/hour")  # Máximo 10 importaciones por hora
async def importar_excel(file: UploadFile):
    # ... lógica de importación
    pass
```

---

### 4. **Autenticación**

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends, HTTPException

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != "MI_TOKEN_SECRETO":
        raise HTTPException(status_code=401, detail="Token inválido")

@app.post("/api/importar-excel")
async def importar_excel(
    file: UploadFile = File(...),
    token: str = Depends(verify_token)
):
    # ... lógica protegida
    pass
```

---

### 5. **Logs Estructurados**

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('importar_dgii.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@app.post("/api/importar-excel")
async def importar_excel(file: UploadFile):
    logger.info(f"Iniciando importación: {file.filename}")
    try:
        # ... lógica
        logger.info(f"Importación exitosa: {head_count} registros")
    except Exception as e:
        logger.error(f"Error en importación: {str(e)}", exc_info=True)
        raise
```

---

## Ejemplo Completo: Flask API

```python
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import tempfile
import os

from core.excel_loader import load_excel
from core.db_manager import (
    ensure_database_exists,
    ensure_tables_exist,
    split_dataframe,
    insert_dataframes,
    test_connection
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max

@app.route('/api/importar', methods=['POST'])
def importar():
    # Validar archivo
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.xlsx'):
        return jsonify({'error': 'Only .xlsx files allowed'}), 400
    
    # Parámetros opcionales
    recreate = request.form.get('recreate', 'false').lower() == 'true'
    
    # Guardar temporal
    filename = secure_filename(file.filename)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name
    
    try:
        # Validar conexión
        success, error = test_connection()
        if not success:
            return jsonify({'error': f'DB connection failed: {error}'}), 500
        
        # Procesar
        ensure_database_exists()
        df = load_excel(tmp_path)
        ensure_tables_exist(df, recreate_mode=recreate)
        df_head, det_tables = split_dataframe(df)
        head_count, detail_counts = insert_dataframes(df_head, det_tables)
        
        return jsonify({
            'success': True,
            'file': filename,
            'encabezados': head_count,
            'detalles': sum(detail_counts.values()),
            'tablas': detail_counts
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.route('/api/health', methods=['GET'])
def health():
    success, error = test_connection()
    if success:
        return jsonify({'status': 'healthy', 'database': 'connected'})
    else:
        return jsonify({'status': 'unhealthy', 'error': error}), 503

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

**Ejecutar:**
```bash
python app.py
```

**Probar:**
```bash
curl -X POST http://localhost:5000/api/importar \
  -F "file=@facturas.xlsx" \
  -F "recreate=false"
```

---

## Despliegue en Producción

### Servidor Web: Gunicorn (Linux)

```bash
# Instalar
pip install gunicorn

# Ejecutar (4 workers)
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

---

### Servidor Web: Waitress (Windows)

```bash
# Instalar
pip install waitress

# Ejecutar
waitress-serve --port=8000 app:app
```

---

### Docker Container

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

# Instalar driver ODBC
RUN apt-get update && apt-get install -y \
    curl apt-transport-https gnupg unixodbc-dev && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18

WORKDIR /app

# Copiar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código (sin UI)
COPY core/ ./core/
COPY config/ ./config/
COPY app.py .

EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
```

**Construir y ejecutar:**
```bash
docker build -t importar-dgii-api .
docker run -p 8000:8000 \
  -v $(pwd)/config:/app/config \
  importar-dgii-api
```

---

## Variables de Entorno (Recomendado)

**Modificar `db_manager.py` para soportar env vars:**

```python
import os

def load_settings() -> Dict[str, str]:
    # Priorizar variables de entorno
    return {
        "server": os.getenv("DB_SERVER", "localhost"),
        "database": os.getenv("DB_NAME", "ImportarFE"),
        "user": os.getenv("DB_USER", "SISTEMA"),
        "password": os.getenv("DB_PASSWORD", "@@sistema"),
        "driver": os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server"),
        "table_encabezado": os.getenv("TABLE_ENCABEZADO", "FEEncabezado"),
        "table_detalle_prefix": os.getenv("TABLE_DETALLE_PREFIX", "FEDetalle"),
        "validate_duplicates": os.getenv("VALIDATE_DUPLICATES", "true").lower() == "true"
    }
```

**Archivo `.env`:**
```env
DB_SERVER=sql-server.example.com
DB_NAME=ImportarFE
DB_USER=api_user
DB_PASSWORD=SecurePassword123
DB_DRIVER=ODBC Driver 17 for SQL Server
VALIDATE_DUPLICATES=true
```

**Cargar con python-dotenv:**
```bash
pip install python-dotenv
```

```python
from dotenv import load_dotenv
load_dotenv()  # Cargar .env al inicio de app.py
```

---

## Resumen de Funciones Principales

| Función | Módulo | Propósito |
|---------|--------|-----------|
| `load_excel()` | `excel_loader.py` | Cargar y limpiar Excel |
| `load_settings()` | `db_manager.py` | Leer configuración JSON |
| `save_settings()` | `db_manager.py` | Guardar configuración JSON |
| `ensure_database_exists()` | `db_manager.py` | Crear BD si no existe |
| `ensure_tables_exist()` | `db_manager.py` | Crear/sincronizar tablas |
| `split_dataframe()` | `db_manager.py` | Dividir en encabezado/detalle |
| `insert_dataframes()` | `db_manager.py` | Insertar datos en SQL Server |
| `test_connection()` | `db_manager.py` | Probar conexión a BD |

---

## Soporte y Contacto

**Sistema:** ImportarDGII v4  
**Propósito:** Importación de Facturación Electrónica DGII a SQL Server  
**Licencia:** Uso interno - ASESYS  

Para preguntas técnicas o reportar errores, contactar al equipo de desarrollo.

---

## Changelog

### v4.0 (2024)
- ✅ Soporte para validación de duplicados por `ENCF` + `RNCEmisor`
- ✅ Transposición automática de columnas indexadas `[1]`, `[2]`, `[3]`...
- ✅ Sincronización inteligente de esquemas sin pérdida de datos
- ✅ Conversión automática de tipos según definiciones JSON
- ✅ Filtrado de ítems sin `CantidadItem` válida
- ✅ Normalización de nombres de columnas (remover corchetes)
- ✅ Logs estructurados con emojis/códigos ASCII
- ✅ Modo recrear vs modo agregar
- ✅ Columnas automáticas `fechacreacion` y `Modificado`

---

## Licencia

Copyright © 2024 ASESYS. Todos los derechos reservados.

Este sistema es propiedad de ASESYS y está destinado exclusivamente para uso interno. Queda prohibida su distribución, modificación o uso comercial sin autorización expresa.
