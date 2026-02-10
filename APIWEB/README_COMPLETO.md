# 📚 Documentación Completa - Sistema API FEDGII

**Versión:** 2.0  
**Última actualización:** Octubre 2025  
**Autor:** Sistema de Facturación Electrónica FEDGII

---

## 📑 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Inicio Rápido (5 minutos)](#inicio-rápido-5-minutos)
3. [Estructura de Carpetas por Empresa](#estructura-de-carpetas-por-empresa)
4. [Sistema de Gestión de Queries SQL](#sistema-de-gestión-de-queries-sql)
5. [Sistema de Gestión de Manuales PDF](#sistema-de-gestión-de-manuales-pdf)
6. [Sistema de Tickets de Incidencias](#sistema-de-tickets-de-incidencias)
7. [Sistema de Importación de Facturas](#sistema-de-importación-de-facturas)
8. [Seguridad y Autenticación](#seguridad-y-autenticación)
9. [Testing y Verificación](#testing-y-verificación)
10. [Troubleshooting](#troubleshooting)
11. [Consideraciones de Producción](#consideraciones-de-producción)

---

## 🎯 Introducción

Este sistema es una API completa para la gestión de facturación electrónica en República Dominicana, incluyendo:

- ✅ **Gestión de empresas con RNC**
- ✅ **Estructura de carpetas automática por empresa**
- ✅ **Sistema de queries SQL reutilizables**
- ✅ **Gestión de manuales y documentación PDF**
- ✅ **Sistema de tickets de soporte**
- ✅ **Importación masiva de facturas desde Excel/CSV**
- ✅ **Autenticación JWT y API Keys**
- ✅ **Logging y auditoría completa**

### 📊 Estadísticas del Proyecto

| Métrica | Valor |
|---------|-------|
| **Endpoints implementados** | 50+ endpoints |
| **Archivos de código** | 15+ archivos |
| **Líneas de código** | ~5000+ líneas |
| **Tests unitarios** | 30+ tests |
| **Sistemas integrados** | 6 subsistemas |

---

## 🚀 Inicio Rápido (5 minutos)

### 1️⃣ Crear Directorios Necesarios (PowerShell como Admin)

```powershell
# Crear directorios base
New-Item -Path "C:\Query" -ItemType Directory -Force
New-Item -Path "C:\Manuales" -ItemType Directory -Force
New-Item -Path "C:\Tickets\Attachments" -ItemType Directory -Force
New-Item -Path "C:\XMLvalidar" -ItemType Directory -Force

# Configurar permisos
icacls "C:\Query" /grant Users:(OI)(CI)F
icacls "C:\Manuales" /grant Users:(OI)(CI)F
icacls "C:\Tickets" /grant Users:(OI)(CI)F
icacls "C:\XMLvalidar" /grant Users:(OI)(CI)F
```

### 2️⃣ Verificar Instalación

```bash
cd C:\Users\urena\Python\src\fedgii\APIWEB
python verify_setup.py
```

**Salida esperada:**
```
✅ PASS - Directorio C:\Query\
✅ PASS - Directorio C:\Manuales\
✅ PASS - Directorio C:\Tickets\Attachments\
✅ PASS - Tabla sql_queries
✅ PASS - Tabla manuales
✅ PASS - Tabla tickets
✅ PASS - Tabla FacturasImportadas
✅ PASS - Funciones de Validación

🎉 ¡Todos los tests pasaron! El sistema está listo para usar.
```

### 3️⃣ Iniciar Servidor

```bash
python run.py
```

**Salida esperada:**
```
Directorio C:\Query\ verificado/creado
Tabla sql_queries verificada/creada
Directorio C:\Manuales\ verificado/creado
Tabla manuales verificada/creada
Directorio C:\Tickets\ verificado/creado
Tabla tickets verificada/creada
Tabla FacturasImportadas verificada/creada
Tablas creadas exitosamente o ya existen.
Iniciando Uvicorn con SSL en https://0.0.0.0:8001
```

### 4️⃣ Obtener Token (Login)

**PowerShell:**
```powershell
$response = Invoke-RestMethod -Uri "https://localhost:8001/login" `
  -Method POST `
  -Body (@{username="admin"; password="tu_password"} | ConvertTo-Json) `
  -ContentType "application/json" `
  -SkipCertificateCheck

$token = $response.token
Write-Host "Token obtenido: $token"
```

### 5️⃣ Verificar que Funciona

```powershell
# Listar empresas
$headers = @{ "Authorization" = "Bearer $token" }
Invoke-RestMethod -Uri "https://localhost:8001/empresas" `
  -Method GET -Headers $headers -SkipCertificateCheck
```

---

## 🏢 Estructura de Carpetas por Empresa

### Descripción

Cada empresa registrada obtiene automáticamente una estructura de carpetas organizada basada en su RNC.

### Estructura Creada

```
C:/XMLvalidar/{RNC}/
├── Img/                    # Imágenes y logos
├── RI/                     # Reportes de ingresos
├── Semillas/               # Archivos semilla
│   ├── Firmadas/
│   └── Generadas/
├── Bin/                    # Binarios y ejecutables
│   └── Servicios/
│       └── Config/         # Archivos de configuración
│           ├── configdgii.json
│           ├── configxsd.json
│           ├── directorios.json
│           └── config.json
├── Token/                  # Tokens de autenticación
├── XML/                    # Archivos XML
│   ├── Firmadas/
│   └── Generadas/
├── Cert/                   # Certificados digitales
└── CSV/                    # Archivos CSV importados
```

### Endpoints Disponibles

#### 1. Registrar Empresa (crea estructura automáticamente)

**POST** `/register_empresa`

```json
{
  "rnc": "131793916",
  "nombre_comercial": "ASESYS",
  "razon_social": "ASESYS SRL"
}
```

#### 2. Verificar Estructura de Empresa

**GET** `/empresa/{rnc}/estructura`

**Response:**
```json
{
  "rnc": "131793916",
  "estructura_existe": true,
  "ruta_empresa": "C:/XMLvalidar/131793916",
  "carpetas_existentes": ["Img", "RI", "Semillas", "Bin", "Token", "XML", "Cert", "CSV"],
  "carpetas_faltantes": [],
  "estructura_completa": true
}
```

#### 3. Obtener Empresas Registradas

**GET** `/empresas`

**Response:**
```json
{
  "empresas": [
    {
      "RNC": "131793916",
      "NombreComercial": "ASESYS",
      "RazonSocial": "ASESYS SRL",
      "Valido": true,
      "Logo": "logo.png"
    }
  ]
}
```

### Ejemplo de Uso

```powershell
# Crear empresa
$body = @{
    rnc = "131793916"
    nombre_comercial = "ASESYS"
    razon_social = "ASESYS SRL"
} | ConvertTo-Json

$headers = @{ "Authorization" = "Bearer $token" }

$empresa = Invoke-RestMethod -Uri "https://localhost:8001/register_empresa" `
  -Method POST -Headers $headers -Body $body `
  -ContentType "application/json" -SkipCertificateCheck

# Verificar estructura creada
Invoke-RestMethod -Uri "https://localhost:8001/empresa/131793916/estructura" `
  -Method GET -Headers $headers -SkipCertificateCheck
```

---

## 📝 Sistema de Gestión de Queries SQL

### Descripción

Sistema para almacenar, gestionar y reutilizar queries SQL de SQL Server desde la pestaña "Soporte" de la aplicación web.

### Características

- ✅ Almacenamiento dual: Base de datos + archivos `.txt` en `C:\Query\`
- ✅ Validación y sanitización de inputs
- ✅ Prevención de SQL injection y path traversal
- ✅ Backups automáticos al actualizar
- ✅ Filtros y paginación
- ✅ 8 tipos de queries soportados

### Tipos de Queries Soportados

- `SELECT` - Consultas de selección
- `UPDATE` - Actualizaciones de datos
- `INSERT` - Inserción de datos
- `DELETE` - Eliminación de datos
- `VIEW` - Vistas de base de datos
- `PROCEDURE` - Procedimientos almacenados
- `FUNCTION` - Funciones de base de datos
- `OTHER` - Otros tipos

### API Endpoints

#### 1. Crear Query

**POST** `/api/queries`

**Body:**
```json
{
  "nombre": "ConsultaClientesActivos",
  "tipo": "SELECT",
  "finalidad": "Reporte mensual de clientes",
  "empresa": "ACME Corp",
  "query_text": "SELECT id, nombre, email FROM clientes WHERE activo = 1"
}
```

**Response (201):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "nombre": "ConsultaClientesActivos",
  "tipo": "SELECT",
  "finalidad": "Reporte mensual de clientes",
  "empresa": "ACME Corp",
  "filename": "123e4567_ConsultaClientesActivos.txt",
  "created_at": "2025-10-15T12:34:56Z",
  "updated_at": "2025-10-15T12:34:56Z",
  "created_by": "usuario123"
}
```

#### 2. Listar Queries

**GET** `/api/queries?tipo=SELECT&empresa=ACME&limit=10`

**Response (200):**
```json
{
  "total": 42,
  "limit": 10,
  "offset": 0,
  "items": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "nombre": "ConsultaClientesActivos",
      "tipo": "SELECT",
      "empresa": "ACME Corp",
      "created_at": "2025-10-15T12:34:56Z"
    }
  ]
}
```

#### 3. Obtener Query por ID

**GET** `/api/queries/{id}`

#### 4. Actualizar Query

**PUT** `/api/queries/{id}`

#### 5. Eliminar Query

**DELETE** `/api/queries/{id}`

### Ejemplo Completo

```powershell
# 1. Crear query
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

$body = @{
    nombre = "ListadoUsuarios"
    tipo = "SELECT"
    finalidad = "Consulta de usuarios activos"
    empresa = "ASESYS"
    query_text = "SELECT * FROM usuarios WHERE estado = 1"
} | ConvertTo-Json

$query = Invoke-RestMethod -Uri "https://localhost:8001/api/queries" `
  -Method POST -Headers $headers -Body $body -SkipCertificateCheck

# 2. Listar queries
$queries = Invoke-RestMethod -Uri "https://localhost:8001/api/queries?limit=10" `
  -Method GET -Headers $headers -SkipCertificateCheck

$queries.items | Format-Table -Property nombre, tipo, empresa

# 3. Verificar archivo creado
Get-ChildItem C:\Query\*.txt | Select-Object Name, Length, LastWriteTime
```

### Seguridad

- **Path Traversal Prevention:** Nombres sanitizados automáticamente
- **SQL Injection Prevention:** Prepared statements con parámetros
- **Tamaños Máximos:** Nombre 100 chars, Query 20,000 chars
- **Logging Completo:** Todas las operaciones registradas

---

## 📚 Sistema de Gestión de Manuales PDF

### Descripción

Sistema para subir, descargar y visualizar manuales/instructivos en formato PDF desde la pestaña "Soporte".

### Características

- ✅ Upload de archivos PDF (máx 50MB)
- ✅ Descarga y visualización inline
- ✅ Categorización (USUARIO, TECNICO, ADMINISTRADOR, etc.)
- ✅ Contador de descargas/visualizaciones
- ✅ Validación de archivos PDF (firma `%PDF`)
- ✅ Metadata en base de datos

### Categorías Válidas

- `USUARIO` - Manuales para usuarios finales
- `TECNICO` - Documentación técnica
- `ADMINISTRADOR` - Guías de administración
- `CONFIGURACION` - Manuales de configuración
- `API` - Documentación de API
- `OTRO` - Otros tipos

### API Endpoints

#### 1. Subir Manual

**POST** `/api/manuales`

**Content-Type:** `multipart/form-data`

**Form Data:**
```
file: <archivo PDF> (obligatorio, máx 50MB)
nombre: "Manual de Usuario" (obligatorio, 3-150 caracteres)
categoria: "USUARIO" (opcional)
descripcion: "Guía completa" (opcional, máx 500 caracteres)
version: "1.0" (opcional)
```

**Response (201):**
```json
{
  "id": "a7f3e9c2-4b1d-4a3e-8f2c-1d9e7b6a5c4d",
  "nombre": "Manual de Usuario",
  "categoria": "USUARIO",
  "descripcion": "Guía completa para usuarios finales",
  "filename": "a7f3e9c2_Manual_de_Usuario.pdf",
  "file_size": 2457600,
  "file_size_mb": 2.34,
  "version": "1.0",
  "download_count": 0
}
```

#### 2. Listar Manuales

**GET** `/api/manuales?categoria=USUARIO&limit=10`

#### 3. Descargar Manual

**GET** `/api/manuales/{id}/download`

Descarga el archivo PDF. Incrementa contador de descargas.

#### 4. Visualizar Manual (Inline)

**GET** `/api/manuales/{id}/view`

Visualiza el PDF en el navegador sin descargarlo.

#### 5. Eliminar Manual

**DELETE** `/api/manuales/{id}`

### Ejemplo de Uso

```powershell
# Subir manual PDF
$headers = @{ "Authorization" = "Bearer $token" }

$filePath = "C:\path\to\manual_usuario.pdf"
$formData = @{
    file = Get-Item -Path $filePath
    nombre = "Manual de Usuario V1.0"
    categoria = "USUARIO"
    descripcion = "Guía completa"
    version = "1.0"
}

$manual = Invoke-RestMethod -Uri "https://localhost:8001/api/manuales" `
  -Method POST -Headers $headers -Form $formData -SkipCertificateCheck

Write-Host "Manual creado con ID: $($manual.id)"

# Listar manuales
$manuales = Invoke-RestMethod `
  -Uri "https://localhost:8001/api/manuales?categoria=USUARIO&limit=10" `
  -Method GET -Headers $headers -SkipCertificateCheck

$manuales.items | Format-Table -Property nombre, categoria, file_size_mb, download_count
```

### Validaciones de Seguridad

- **Firma PDF:** Verifica que comience con `%PDF`
- **Extensión:** Solo `.pdf` permitido
- **Tamaño:** Máximo 50 MB, mínimo 100 bytes
- **Path Traversal:** Nombres sanitizados
- **Almacenamiento:** Aislado en `C:\Manuales\`

---

## 🎫 Sistema de Tickets de Incidencias

### Descripción

Sistema completo de gestión de tickets de soporte con adjuntos de archivos.

### Características

- ✅ Crear, listar, actualizar y eliminar tickets
- 📁 Adjuntar múltiples archivos (max 5 por upload)
- 🔍 Filtros avanzados y ordenamiento
- 📊 Estadísticas del sistema
- 🔒 Validación de archivos adjuntos

### Prioridades y Estados

**Prioridades:**
- `BAJA` (score: 1)
- `MEDIA` (score: 2)
- `ALTA` (score: 3)
- `CRÍTICA` (score: 4)

⚠️ **Nota:** Se acepta tanto 'CRITICA' (sin tilde) como 'CRÍTICA' (con tilde). Ambas formas se normalizan a 'CRÍTICA'.

**Estados:**
- `PENDIENTE` - Ticket nuevo
- `EN_PROGRESO` - En atención
- `RESUELTO` - Solución implementada
- `CERRADO` - Ticket cerrado

### API Endpoints

#### 1. Crear Ticket con Adjuntos

**POST** `/api/tickets`

**Content-Type:** `multipart/form-data`

**Form Data:**
```
titulo: "Error en módulo X" (requerido, max 200)
prioridad: "ALTA" (requerido)
categoria: "Bug" (requerido, max 100)
empresa: "ASESYS" (opcional, max 200)
descripcion: "Descripción detallada" (requerido)
creado_por: "juan.perez" (requerido)
asignado_a: "soporte.tecnico" (opcional)
attachments: file[] (opcional, max 5 archivos)
```

**Response (201):**
```json
{
  "id": "ticket-uuid",
  "titulo": "Error en módulo X",
  "prioridad": "ALTA",
  "categoria": "Bug",
  "empresa": "ASESYS",
  "descripcion": "Descripción detallada...",
  "estado": "PENDIENTE",
  "creado_por": "juan.perez",
  "asignado_a": "soporte.tecnico",
  "prioridad_score": 3,
  "created_at": "2025-10-17T10:30:00",
  "attachments": [
    {
      "id": "attachment-uuid",
      "filename": "uuid_screenshot.png",
      "original_name": "screenshot.png",
      "content_type": "image/png",
      "size_bytes": 245000
    }
  ]
}
```

#### 2. Listar Tickets con Filtros

**GET** `/api/tickets?estado=PENDIENTE&prioridad=ALTA&limit=50`

**Query Parameters:**
- `estado` - Filtrar por estado (ALL para todos)
- `prioridad` - Filtrar por prioridad
- `categoria` - Filtrar por categoría
- `empresa` - Filtrar por empresa
- `creado_por` - Filtrar por creador
- `asignado_a` - Filtrar por asignado
- `search` - Buscar en título y descripción
- `limit` - Registros por página (default: 50)
- `offset` - Desplazamiento para paginación
- `sort` - Ordenamiento (ej: `priority_score:desc,created_at:asc`)

#### 3. Obtener Detalle de Ticket

**GET** `/api/tickets/{id}`

#### 4. Actualizar Ticket

**PUT** `/api/tickets/{id}`

```json
{
  "titulo": "Nuevo título",
  "prioridad": "CRÍTICA",
  "estado": "EN_PROGRESO",
  "asignado_a": "nuevo.responsable"
}
```

#### 5. Eliminar Ticket

**DELETE** `/api/tickets/{id}`

#### 6. Agregar Adjuntos

**POST** `/api/tickets/{id}/attachments`

#### 7. Descargar Adjunto

**GET** `/api/tickets/attachments/{attachment_id}`

#### 8. Estadísticas

**GET** `/api/tickets/stats`

**Response:**
```json
{
  "total_tickets": 150,
  "by_estado": {
    "PENDIENTE": 45,
    "EN_PROGRESO": 30,
    "RESUELTO": 50,
    "CERRADO": 25
  },
  "by_prioridad": {
    "BAJA": 20,
    "MEDIA": 60,
    "ALTA": 50,
    "CRÍTICA": 20
  }
}
```

### Ejemplo de Uso

```powershell
# Crear ticket con adjunto
$headers = @{ "Authorization" = "Bearer $token" }

$formData = @{
    titulo = "Error crítico en facturación"
    prioridad = "CRITICA"  # También acepta "CRÍTICA"
    categoria = "Bug"
    empresa = "ASESYS"
    descripcion = "Error al generar facturas electrónicas"
    creado_por = "juan.perez"
    asignado_a = "soporte.tecnico"
    attachments = @(
        Get-Item -Path "C:\screenshots\error.png"
        Get-Item -Path "C:\logs\error.log"
    )
}

$ticket = Invoke-RestMethod -Uri "https://localhost:8001/api/tickets" `
  -Method POST -Headers $headers -Form $formData -SkipCertificateCheck

Write-Host "Ticket creado con ID: $($ticket.id)"
```

### Configuración de Archivos

- **Tamaño máximo por archivo:** 10 MB
- **Tamaño total máximo:** 50 MB
- **Máximo archivos por upload:** 5
- **Extensiones permitidas:** .pdf, .jpg, .jpeg, .png, .txt, .docx, .xlsx, .zip
- **Extensiones prohibidas:** .exe, .bat, .cmd, .ps1, .sh

---

## 📊 Sistema de Importación de Facturas

### Descripción

Sistema para importar facturas masivamente desde archivos Excel (.xlsx, .xls) o CSV por empresa (RNC).

### Características

- ✅ Importación desde Excel y CSV
- ✅ Actualización automática de registros existentes (por ENCF)
- ✅ Validación de datos y conversión automática de tipos
- ✅ Mapeo inteligente de columnas
- ✅ Estadísticas por empresa
- ✅ Tabla SQL Server con verificación automática

### Tabla: FacturasImportadas

**Campos:**
- `RNC_Empresa` (NVARCHAR(20)) - RNC de la empresa propietaria
- `RNC_Receptor` (NVARCHAR(20)) - RNC del receptor
- `ENCF` (NVARCHAR(19)) - Número de comprobante fiscal (ÚNICO por empresa)
- `ENCF_Modificado` (NVARCHAR(19)) - NCF modificado
- `Fecha_Comprobante` (DATE) - Fecha del comprobante
- `Fecha_Recepcion` (DATE) - Fecha de recepción
- `Aprobacion_Comercial` (BIT) - Sí/No aprobación
- `Fecha_Aprobacion_Comercial` (DATE) - Fecha de aprobación
- `Estado` (NVARCHAR(50)) - Estado del comprobante
- `ITBIS_Facturado` (DECIMAL(18,2)) - Monto ITBIS
- `Monto_Total_Gravado` (DECIMAL(18,2)) - Monto gravado
- `Monto_Exento` (DECIMAL(18,2)) - Monto exento
- `Monto_No_Facturable` (DECIMAL(18,2)) - Monto no facturable
- `Fecha_Importacion` (DATETIME) - Fecha de importación

**Constraint:** UNIQUE (RNC_Empresa, ENCF) - El ENCF es único por empresa

### Mapeo de Columnas

El sistema reconoce automáticamente estas variaciones de nombres:

| Nombre en Excel/CSV | Columna en DB |
|---------------------|---------------|
| "RNC Receptor", "RNC", "Receptor" | RNC_Receptor |
| "ENCF", "E-NCF", "NCF", "Numero Comprobante" | ENCF |
| "ENCF Modificado", "NCF Modificado" | ENCF_Modificado |
| "Fecha Comprobante", "Fecha" | Fecha_Comprobante |
| "Fecha Recepcion", "Fecha Recepción" | Fecha_Recepcion |
| "Aprobacion Comercial", "Aprobación Comercial" | Aprobacion_Comercial |
| "Estado" | Estado |
| "ITBIS Facturado", "ITBIS" | ITBIS_Facturado |
| "Monto Total Gravado", "Total Gravado", "Gravado" | Monto_Total_Gravado |
| "Monto Exento", "Exento" | Monto_Exento |
| "Monto No Facturable", "No Facturable" | Monto_No_Facturable |

### API Endpoints

#### 1. Importar Facturas

**POST** `/empresa/{rnc}/importar-facturas`

**Content-Type:** `multipart/form-data`

**Form Data:**
```
archivo: <archivo Excel o CSV> (obligatorio)
```

**Formato del archivo:**

Puede usar cualquiera de estas variaciones de nombres de columnas (no case-sensitive):

```
| RNC Receptor | ENCF          | Fecha Comprobante | ITBIS Facturado | Monto Total Gravado | Estado    |
|--------------|---------------|-------------------|-----------------|---------------------|-----------|
| 131793916    | E310000000001 | 2025-01-15        | 1800.00         | 10000.00            | Aprobado  |
| 101234567    | E310000000002 | 2025-01-16        | 540.00          | 3000.00             | Pendiente |
```

**Response (200):**
```json
{
  "message": "Facturas importadas exitosamente",
  "archivo": "import_1729234567_facturas.xlsx",
  "registros_procesados": 100,
  "registros_nuevos": 50,
  "registros_actualizados": 50,
  "errores": []
}
```

**Comportamiento:**
- Si el ENCF existe para ese RNC, **actualiza** el registro
- Si el ENCF no existe, **crea** un nuevo registro
- Las fechas se convierten automáticamente
- Los montos se convierten a numéricos (default: 0)
- Aprobación Comercial acepta: "si", "sí", "s", "yes", "y", "1", "true"

#### 2. Consultar Facturas

**GET** `/empresa/{rnc}/facturas?limit=100&offset=0`

**Query Parameters:**
- `limit` - Registros por página (default: 100)
- `offset` - Desplazamiento para paginación
- `encf` - Filtrar por ENCF (búsqueda parcial)
- `fecha_desde` - Filtrar desde fecha (YYYY-MM-DD)
- `fecha_hasta` - Filtrar hasta fecha (YYYY-MM-DD)
- `estado` - Filtrar por estado

**Response (200):**
```json
{
  "rnc": "131793916",
  "total": 1000,
  "limit": 100,
  "offset": 0,
  "facturas": [
    {
      "Id": 1,
      "RNC_Empresa": "131793916",
      "RNC_Receptor": "101234567",
      "ENCF": "E310000000001",
      "ENCF_Modificado": "",
      "Fecha_Comprobante": "2025-01-15",
      "Fecha_Recepcion": "2025-01-16",
      "Aprobacion_Comercial": true,
      "Fecha_Aprobacion_Comercial": "2025-01-17",
      "Estado": "Aprobado",
      "ITBIS_Facturado": 1800.00,
      "Monto_Total_Gravado": 10000.00,
      "Monto_Exento": 0.00,
      "Monto_No_Facturable": 0.00,
      "Fecha_Importacion": "2025-01-20T10:30:00"
    }
  ]
}
```

#### 3. Eliminar Factura

**DELETE** `/empresa/{rnc}/factura/{encf}`

**Response (200):**
```json
{
  "message": "Factura eliminada exitosamente",
  "encf": "E310000000001"
}
```

#### 4. Estadísticas de Facturas

**GET** `/empresa/{rnc}/facturas/estadisticas`

**Response (200):**
```json
{
  "rnc": "131793916",
  "total_facturas": 1000,
  "por_estado": {
    "Aprobado": 800,
    "Pendiente": 150,
    "Rechazado": 50
  },
  "totales_montos": {
    "total_itbis": 1500000.00,
    "total_gravado": 8500000.00,
    "total_exento": 200000.00,
    "total_no_facturable": 50000.00
  },
  "ultima_importacion": "2025-10-20T10:30:00"
}
```

### Ejemplo de Uso Completo

```powershell
# 1. Preparar archivo Excel con facturas
# Columnas: RNC Receptor, ENCF, Fecha Comprobante, ITBIS Facturado, etc.

# 2. Importar facturas
$headers = @{ "Authorization" = "Bearer $token" }
$rnc = "131793916"
$filePath = "C:\datos\facturas_enero_2025.xlsx"

$formData = @{
    archivo = Get-Item -Path $filePath
}

$resultado = Invoke-RestMethod `
  -Uri "https://localhost:8001/empresa/$rnc/importar-facturas" `
  -Method POST `
  -Headers $headers `
  -Form $formData `
  -SkipCertificateCheck

Write-Host "Importación completada:"
Write-Host "  Registros procesados: $($resultado.registros_procesados)"
Write-Host "  Nuevos: $($resultado.registros_nuevos)"
Write-Host "  Actualizados: $($resultado.registros_actualizados)"

# 3. Consultar facturas importadas
$facturas = Invoke-RestMethod `
  -Uri "https://localhost:8001/empresa/$rnc/facturas?limit=10" `
  -Method GET `
  -Headers $headers `
  -SkipCertificateCheck

$facturas.facturas | Format-Table -Property ENCF, Fecha_Comprobante, Estado, ITBIS_Facturado

# 4. Ver estadísticas
$stats = Invoke-RestMethod `
  -Uri "https://localhost:8001/empresa/$rnc/facturas/estadisticas" `
  -Method GET `
  -Headers $headers `
  -SkipCertificateCheck

Write-Host "`nEstadísticas:"
Write-Host "  Total facturas: $($stats.total_facturas)"
Write-Host "  Total ITBIS: $($stats.totales_montos.total_itbis)"
Write-Host "  Total Gravado: $($stats.totales_montos.total_gravado)"
```

### Manejo de Errores

El sistema registra errores por fila y los retorna (máximo 10 en la respuesta):

```json
{
  "errores": [
    "Fila 15: ENCF es requerido",
    "Fila 23: Fecha inválida en Fecha_Comprobante"
  ]
}
```

### Archivo Importado

El archivo se guarda automáticamente en: `C:\XMLvalidar\{RNC}\CSV\import_{timestamp}_{filename}`

---

## 🔒 Seguridad y Autenticación

### Autenticación JWT

Todos los endpoints protegidos requieren token JWT en el header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Obtener Token

**POST** `/login`

```json
{
  "username": "admin",
  "password": "tu_password"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "username": "admin"
}
```

### API Keys

Alternativa a JWT para integraciones:

**POST** `/generate-api-key`

```
Authorization: Bearer <tu_token_jwt>
```

**Response:**
```json
{
  "api_key": "tu_api_key_generada_aqui..."
}
```

**Uso:**
```
X-API-Key: tu_api_key_generada_aqui...
```

### Validaciones de Seguridad

#### 1. Path Traversal Prevention
```python
# Bloquea: ../../etc/passwd, ..\windows\system32, etc.
# Caracteres bloqueados: .., /, \, :, *, ?, ", <>, |
```

#### 2. SQL Injection Prevention
```python
# Uso de prepared statements con parámetros
cursor.execute("SELECT * FROM tabla WHERE id = ?", id)
```

#### 3. Validación de Archivos

**PDF (Manuales):**
- Firma `%PDF` al inicio del archivo
- Extensión `.pdf` únicamente
- Tamaño: 100 bytes a 50 MB

**Adjuntos (Tickets):**
- Extensiones permitidas: .pdf, .jpg, .png, .txt, .docx, .xlsx, .zip
- Extensiones bloqueadas: .exe, .bat, .cmd, .ps1, .sh
- Tamaño máximo: 10 MB por archivo, 50 MB total

**Excel/CSV (Facturas):**
- Extensiones: .xlsx, .xls, .csv
- Validación de estructura de datos

#### 4. Sanitización de Nombres

```python
# Nombres de archivo seguros
# "Mi Documento.pdf" → "Mi_Documento.pdf"
# "Query (test).txt" → "Query_test.txt"
```

### Logging y Auditoría

Todas las operaciones se registran en `APIWEB/data/api.log`:

```
[2025-10-20 10:30:00] INFO: Usuario 'admin' autenticado exitosamente
[2025-10-20 10:31:15] INFO: Query creado por usuario123: 123e4567-...
[2025-10-20 10:32:30] INFO: Manual subido por admin: Manual_Usuario.pdf
[2025-10-20 10:33:45] INFO: Ticket creado por juan.perez: ticket-uuid
[2025-10-20 10:34:50] INFO: Importadas 100 facturas para RNC 131793916
[2025-10-20 10:35:10] WARNING: Intento de path traversal detectado
[2025-10-20 10:36:00] ERROR: Error al procesar archivo: archivo corrupto
```

---

## 🧪 Testing y Verificación

### Tests Disponibles

#### 1. Verificación de Setup

```bash
python verify_setup.py
```

**Verifica:**
- Directorios creados y permisos correctos
- Tablas de base de datos existentes
- Funciones de validación funcionando
- Operaciones de archivos correctas
- Medidas de seguridad activas

#### 2. Tests de Queries

```bash
python test_queries.py
```

**19 Tests:**
- Validación de datos
- Sanitización de nombres
- Path traversal prevention
- Límites de longitud
- Tipos de query válidos
- Caracteres especiales Windows

#### 3. Tests de Manuales

```bash
python test_manuales.py
```

**Tests:**
- Validación de PDF
- Categorías válidas
- Límites de tamaño
- Prevención de path traversal

#### 4. Tests de Tickets

```bash
python test_tickets.py
```

**Tests:**
- Creación de tickets
- Adjuntos de archivos
- Validación de prioridades y estados
- Filtros y ordenamiento

### Ejemplo de Salida de Tests

```
test_ensure_query_directory ... ok
test_validate_query_data_valid ... ok
test_sanitize_filename_path_traversal ... ok
test_pdf_signature_validation ... ok
test_ticket_priority_normalization ... ok
...

----------------------------------------------------------------------
Ran 50 tests in 2.345s

OK
```

### Checklist de Validación Completa

```powershell
# Script completo de validación
Write-Host "=== Validación Completa del Sistema ===" -ForegroundColor Green

# 1. Verificar directorios
$dirs = @("C:\Query", "C:\Manuales", "C:\Tickets\Attachments", "C:\XMLvalidar")
foreach ($dir in $dirs) {
    if (Test-Path $dir) {
        Write-Host "✅ $dir existe" -ForegroundColor Green
    } else {
        Write-Host "❌ $dir NO existe" -ForegroundColor Red
    }
}

# 2. Ejecutar tests
Write-Host "`n=== Ejecutando Tests ===" -ForegroundColor Green
python verify_setup.py
python test_queries.py
python test_manuales.py
python test_tickets.py

# 3. Verificar servidor
Write-Host "`n=== Verificando Servidor ===" -ForegroundColor Green
$testConnection = Test-NetConnection -ComputerName localhost -Port 8001
if ($testConnection.TcpTestSucceeded) {
    Write-Host "✅ Servidor corriendo en puerto 8001" -ForegroundColor Green
} else {
    Write-Host "❌ Servidor NO está corriendo" -ForegroundColor Red
}

# 4. Test de autenticación
Write-Host "`n=== Test de Autenticación ===" -ForegroundColor Green
try {
    $response = Invoke-RestMethod -Uri "https://localhost:8001/login" `
      -Method POST `
      -Body (@{username="admin"; password="test"} | ConvertTo-Json) `
      -ContentType "application/json" `
      -SkipCertificateCheck -ErrorAction Stop
    
    Write-Host "✅ Autenticación funcionando" -ForegroundColor Green
    $token = $response.token
    
    # 5. Test de endpoints
    Write-Host "`n=== Test de Endpoints ===" -ForegroundColor Green
    $headers = @{ "Authorization" = "Bearer $token" }
    
    $endpoints = @(
        "https://localhost:8001/empresas"
        "https://localhost:8001/api/queries?limit=1"
        "https://localhost:8001/api/manuales?limit=1"
        "https://localhost:8001/api/tickets?limit=1"
    )
    
    foreach ($endpoint in $endpoints) {
        try {
            Invoke-RestMethod -Uri $endpoint -Headers $headers -SkipCertificateCheck -ErrorAction Stop | Out-Null
            Write-Host "✅ $endpoint" -ForegroundColor Green
        } catch {
            Write-Host "❌ $endpoint" -ForegroundColor Red
        }
    }
    
} catch {
    Write-Host "❌ Error en autenticación" -ForegroundColor Red
}

Write-Host "`n=== Validación Completada ===" -ForegroundColor Green
```

---

## 🔧 Troubleshooting

### Problemas Comunes y Soluciones

#### 1. Error: "Cannot bind to port 8001"

**Causa:** Puerto ya en uso

**Solución:**
```powershell
# Verificar qué proceso usa el puerto
Get-NetTCPConnection -LocalPort 8001 | Select-Object OwningProcess

# Detener proceso
Stop-Process -Id <PID>
```

#### 2. Error: "Access denied to C:\..."

**Causa:** Falta de permisos

**Solución:**
```powershell
# Como Administrador
icacls "C:\Query" /grant Users:(OI)(CI)F
icacls "C:\Manuales" /grant Users:(OI)(CI)F
icacls "C:\Tickets" /grant Users:(OI)(CI)F
icacls "C:\XMLvalidar" /grant Users:(OI)(CI)F
```

#### 3. Error: "Token expired"

**Causa:** Token JWT expirado

**Solución:**
```powershell
# Hacer login nuevamente
$response = Invoke-RestMethod -Uri "https://localhost:8001/login" `
  -Method POST `
  -Body (@{username="admin"; password="tu_password"} | ConvertTo-Json) `
  -ContentType "application/json" `
  -SkipCertificateCheck

$token = $response.token
```

#### 4. Error: "Cannot connect to database"

**Causa:** Configuración de DB incorrecta

**Solución:**
```powershell
# Verificar cn.ini
Get-Content APIWEB\config\cn.ini

# Editar con credenciales correctas
notepad APIWEB\config\cn.ini
```

#### 5. Error: "El archivo no es un PDF válido"

**Causa:** Archivo corrupto o no es PDF

**Solución:**
- Verificar que el archivo sea PDF real (no renombrado)
- Abrir el archivo en un lector PDF para validar
- Verificar tamaño (debe ser > 100 bytes)

#### 6. Error: "Tabla no existe"

**Causa:** Tabla no creada en base de datos

**Solución:**
```bash
# Reiniciar servidor para crear tablas automáticamente
python run.py
```

#### 7. Error al importar facturas: "Archivo no procesado"

**Causa:** Formato de archivo incorrecto

**Solución:**
- Verificar que sea Excel (.xlsx, .xls) o CSV
- Asegurarse de que tiene columna "ENCF"
- Verificar que las fechas estén en formato válido
- Revisar errores en la respuesta JSON

#### 8. Error: "ENCF duplicado"

**Causa:** Intentando insertar ENCF que ya existe para esa empresa

**Solución:**
El sistema actualiza automáticamente. Si el error persiste:
```sql
-- Verificar registros duplicados
SELECT ENCF, COUNT(*) as cantidad
FROM FacturasImportadas
WHERE RNC_Empresa = '131793916'
GROUP BY ENCF
HAVING COUNT(*) > 1
```

### Verificación de Logs

```powershell
# Ver últimas 50 líneas del log
Get-Content APIWEB\data\api.log -Tail 50

# Filtrar errores
Get-Content APIWEB\data\api.log | Select-String "ERROR"

# Filtrar por fecha
Get-Content APIWEB\data\api.log | Select-String "2025-10-20"
```

### Comandos de Diagnóstico

```powershell
# 1. Verificar espacio en disco
Get-PSDrive C | Select-Object Used, Free

# 2. Verificar directorios y tamaños
Get-ChildItem C:\Query, C:\Manuales, C:\Tickets, C:\XMLvalidar -Recurse | 
  Measure-Object -Property Length -Sum | 
  Select-Object Count, @{Name="SizeMB"; Expression={[math]::Round($_.Sum / 1MB, 2)}}

# 3. Verificar archivos recientes
Get-ChildItem C:\Query -File | Sort-Object LastWriteTime -Descending | Select-Object -First 10

# 4. Contar registros en tablas
# Ejecutar en SQL Server Management Studio
SELECT 
    'sql_queries' as tabla, COUNT(*) as registros FROM sql_queries
UNION ALL
SELECT 'manuales', COUNT(*) FROM manuales
UNION ALL
SELECT 'tickets', COUNT(*) FROM tickets
UNION ALL
SELECT 'ticket_attachments', COUNT(*) FROM ticket_attachments
UNION ALL
SELECT 'FacturasImportadas', COUNT(*) FROM FacturasImportadas
```

---

## 🚀 Consideraciones de Producción

### 1. Backups

```powershell
# Script de backup automático
$fecha = Get-Date -Format "yyyyMMdd_HHmmss"

# Backup de directorios
Copy-Item -Path "C:\Query" -Destination "D:\Backups\Query_$fecha" -Recurse
Copy-Item -Path "C:\Manuales" -Destination "D:\Backups\Manuales_$fecha" -Recurse
Copy-Item -Path "C:\Tickets" -Destination "D:\Backups\Tickets_$fecha" -Recurse
Copy-Item -Path "C:\XMLvalidar" -Destination "D:\Backups\XMLvalidar_$fecha" -Recurse

# Backup de base de datos SQL Server
sqlcmd -S localhost -Q "BACKUP DATABASE [tu_database] TO DISK='D:\Backups\DB_$fecha.bak'"
```

### 2. Monitoreo de Espacio en Disco

```powershell
# Alertar si queda menos de 10GB libres
$drive = Get-PSDrive C
$freeGB = [math]::Round($drive.Free / 1GB, 2)

if ($freeGB -lt 10) {
    Write-Host "⚠️ ALERTA: Solo quedan $freeGB GB libres en C:" -ForegroundColor Red
    # Enviar email de alerta aquí
}
```

### 3. Limpieza de Archivos Antiguos

```powershell
# Eliminar queries más antiguos de 1 año
$fecha_limite = (Get-Date).AddYears(-1)
Get-ChildItem C:\Query -File | 
  Where-Object { $_.LastWriteTime -lt $fecha_limite } | 
  Remove-Item -Force

# Eliminar tickets cerrados más antiguos de 6 meses
$fecha_limite = (Get-Date).AddMonths(-6)
# Implementar lógica en base de datos
```

### 4. Configuración de SSL/TLS

```python
# run.py - Configuración SSL
import ssl

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain('path/to/cert.pem', 'path/to/key.pem')

uvicorn.run(
    app,
    host="0.0.0.0",
    port=8001,
    ssl_keyfile='path/to/key.pem',
    ssl_certfile='path/to/cert.pem'
)
```

### 5. Variables de Entorno

```powershell
# Configurar variables de entorno
[System.Environment]::SetEnvironmentVariable('FEDGII_DB_SERVER', 'localhost', 'Machine')
[System.Environment]::SetEnvironmentVariable('FEDGII_DB_NAME', 'fedgii_db', 'Machine')
[System.Environment]::SetEnvironmentVariable('FEDGII_SECRET_KEY', 'tu_secret_key_aqui', 'Machine')
```

### 6. Límites y Cuotas

```python
# Configurar límites por empresa
MAX_QUERIES_PER_EMPRESA = 1000
MAX_MANUALES_PER_EMPRESA = 100
MAX_TICKETS_PER_EMPRESA = 5000
MAX_STORAGE_PER_EMPRESA_GB = 10
```

### 7. Rate Limiting

```python
# Implementar rate limiting con Flask-Limiter
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.headers.get('X-API-Key'),
    default_limits=["1000 per day", "100 per hour"]
)

@routes.route("/api/queries", methods=["POST"])
@limiter.limit("50 per hour")
def create_query():
    # ...
```

### 8. Logging Avanzado

```python
# Configurar rotación de logs
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'data/api.log',
    maxBytes=10*1024*1024,  # 10 MB
    backupCount=5
)

logger.addHandler(handler)
```

### 9. Monitoreo de Performance

```python
# Middleware para medir tiempo de respuesta
@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    if hasattr(request, 'start_time'):
        duration = time.time() - request.start_time
        if duration > 5:  # Más de 5 segundos
            logger.warning(f"Solicitud lenta: {request.path} - {duration:.2f}s")
    return response
```

### 10. Checklist de Producción

- [ ] ✅ Backups automáticos configurados
- [ ] ✅ Monitoreo de espacio en disco
- [ ] ✅ Limpieza automática de archivos antiguos
- [ ] ✅ SSL/TLS configurado correctamente
- [ ] ✅ Variables de entorno configuradas
- [ ] ✅ Rate limiting implementado
- [ ] ✅ Logging con rotación configurado
- [ ] ✅ Monitoreo de performance activo
- [ ] ✅ Límites y cuotas definidos
- [ ] ✅ Plan de recuperación ante desastres
- [ ] ✅ Documentación actualizada
- [ ] ✅ Tests automatizados pasando

---

## 📞 Soporte y Contacto

### Obtener Ayuda

1. **Consultar esta documentación** - Buscar en las secciones relevantes
2. **Revisar logs** - `APIWEB/data/api.log`
3. **Ejecutar tests** - `python verify_setup.py`
4. **Consultar ejemplos** - Scripts PowerShell incluidos

### Recursos Adicionales

- **Repositorio:** github.com/sanerp4/fedgii
- **Documentos REST:** `ticket_examples.rest`, `r.rest`
- **Scripts PowerShell:** `ticket_scripts.ps1`

### Archivos de Documentación

- `README_COMPLETO.md` - Este archivo (documentación unificada)
- `README_QUERIES.md` - Documentación de queries SQL
- `README_MANUALES.md` - Documentación de manuales PDF
- `README_SISTEMA_TICKETS.md` - Documentación de tickets
- `README_ESTRUCTURA_EMPRESA.md` - Estructura de carpetas
- `INICIO_RAPIDO.md` - Guía de inicio rápido
- `EJEMPLOS_REQUESTS.md` - Ejemplos de requests HTTP

---

## ✅ Checklist Final

### Instalación
- [ ] Python 3.8+ instalado
- [ ] SQL Server configurado
- [ ] Directorios creados (Query, Manuales, Tickets, XMLvalidar)
- [ ] Permisos configurados
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)

### Configuración
- [ ] `config/cn.ini` configurado con conexión a DB
- [ ] Certificados SSL configurados
- [ ] Variables de entorno configuradas

### Verificación
- [ ] `verify_setup.py` pasa todos los tests
- [ ] Tests unitarios pasando
- [ ] Servidor inicia sin errores
- [ ] Login funciona correctamente
- [ ] Endpoints responden correctamente

### Seguridad
- [ ] JWT configurado con secret key fuerte
- [ ] API Keys generándose correctamente
- [ ] Validaciones de archivos activas
- [ ] Path traversal prevention activo
- [ ] Logging de auditoría funcionando

### Producción
- [ ] Backups automáticos configurados
- [ ] Monitoreo de espacio en disco
- [ ] Limpieza automática configurada
- [ ] Rate limiting implementado
- [ ] Plan de recuperación documentado

---

## 🎓 Glosario

| Término | Significado |
|---------|-------------|
| **RNC** | Registro Nacional del Contribuyente (identificador fiscal en RD) |
| **ENCF** | e-Número de Comprobante Fiscal (NCF electrónico) |
| **JWT** | JSON Web Token (método de autenticación) |
| **API Key** | Clave de API para autenticación alternativa |
| **Path Traversal** | Ataque que intenta acceder a directorios fuera del permitido |
| **Sanitización** | Limpieza de inputs para prevenir ataques |
| **UUID** | Identificador único universal |
| **CRUD** | Create, Read, Update, Delete (operaciones básicas) |
| **Endpoint** | URL de la API que responde a requests |
| **ITBIS** | Impuesto sobre Transferencia de Bienes y Servicios (IVA en RD) |
| **PDF** | Portable Document Format |
| **CSV** | Comma-Separated Values |
| **XSD** | XML Schema Definition |

---

## 📊 Resumen de Endpoints

### Autenticación
- `POST /login` - Obtener token JWT
- `POST /generate-api-key` - Generar API Key

### Empresas
- `GET /empresas` - Listar empresas
- `POST /register_empresa` - Registrar empresa
- `GET /empresa/{rnc}/estructura` - Verificar estructura
- `GET /empresa/{rnc}/logo` - Obtener logo
- `PUT /empresa/{rnc}` - Actualizar empresa

### Queries SQL
- `POST /api/queries` - Crear query
- `GET /api/queries` - Listar queries
- `GET /api/queries/{id}` - Obtener query
- `PUT /api/queries/{id}` - Actualizar query
- `DELETE /api/queries/{id}` - Eliminar query

### Manuales PDF
- `POST /api/manuales` - Subir manual
- `GET /api/manuales` - Listar manuales
- `GET /api/manuales/{id}` - Obtener metadata
- `GET /api/manuales/{id}/download` - Descargar manual
- `GET /api/manuales/{id}/view` - Visualizar manual
- `DELETE /api/manuales/{id}` - Eliminar manual

### Tickets
- `POST /api/tickets` - Crear ticket
- `GET /api/tickets` - Listar tickets
- `GET /api/tickets/{id}` - Obtener ticket
- `PUT /api/tickets/{id}` - Actualizar ticket
- `DELETE /api/tickets/{id}` - Eliminar ticket
- `POST /api/tickets/{id}/attachments` - Agregar adjuntos
- `GET /api/tickets/{id}/attachments` - Listar adjuntos
- `GET /api/tickets/attachments/{id}` - Descargar adjunto
- `DELETE /api/tickets/attachments/{id}` - Eliminar adjunto
- `GET /api/tickets/stats` - Estadísticas
- `GET /api/tickets/config` - Configuración

### Facturas
- `POST /empresa/{rnc}/importar-facturas` - Importar facturas
- `GET /empresa/{rnc}/facturas` - Listar facturas
- `DELETE /empresa/{rnc}/factura/{encf}` - Eliminar factura
- `GET /empresa/{rnc}/facturas/estadisticas` - Estadísticas

---

**🎉 ¡Sistema completo y listo para producción!**

*Última actualización: Octubre 2025*
