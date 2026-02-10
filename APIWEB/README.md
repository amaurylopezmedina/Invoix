# 📚 API FEDGII - Sistema de Facturación Electrónica

**Versión:** 3.0  
**Última actualización:** Enero 2026  
**Autor:** Sistema de Facturación Electrónica FEDGII

---

## 📑 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Instalación y Configuración](#instalación-y-configuración)
3. [Sistema de Usuarios](#sistema-de-usuarios)
4. [Sistema de Tickets de Incidencias](#sistema-de-tickets-de-incidencias)
5. [Estructura de Carpetas por Empresa](#estructura-de-carpetas-por-empresa)
6. [Sistema de Gestión de Queries SQL](#sistema-de-gestión-de-queries-sql)
7. [Sistema de Gestión de Manuales PDF](#sistema-de-gestión-de-manuales-pdf)
8. [Autenticación y Seguridad](#autenticación-y-seguridad)
9. [API Endpoints](#api-endpoints)

---

## 🎯 Introducción

Sistema API completo para la gestión de facturación electrónica en República Dominicana, incluyendo:

- ✅ **Gestión de empresas con RNC**
- ✅ **Sistema de usuarios con roles (Admin, Soporte, Facturación, Cliente)**
- ✅ **Portal de clientes para tickets de soporte**
- ✅ **Sistema de tickets de incidencias**
- ✅ **Queries SQL reutilizables**
- ✅ **Gestión de manuales PDF**
- ✅ **Autenticación JWT y API Keys**

### 📊 Estadísticas del Proyecto

| Métrica | Valor |
|---------|-------|
| **Endpoints implementados** | 60+ endpoints |
| **Tipos de usuarios** | 4 tipos |
| **Sistemas integrados** | 7 subsistemas |

---

## 🚀 Instalación y Configuración

### 1️⃣ Crear Entorno Virtual

```powershell
# En la carpeta APIWEB
cd C:\Users\urena\OneDrive\Documentos\WebASESYS\APIWEB

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
.\venv\Scripts\activate
```

### 2️⃣ Instalar Dependencias

```powershell
# Con el entorno virtual activado
pip install -r requirements.txt
```

### 3️⃣ Dependencias (requirements.txt)

```
# Framework Web
flask>=2.3.0
flask-cors>=4.0.0

# Server ASGI
uvicorn[standard]>=0.27.0
starlette>=0.36.0

# Autenticación y Seguridad
PyJWT>=2.8.0
passlib>=1.7.4
cryptography>=41.0.0

# Base de Datos
pyodbc>=5.0.0
SQLAlchemy>=2.0.0

# Procesamiento de Archivos
python-multipart>=0.0.6
werkzeug>=3.0.0
pandas>=2.0.0
openpyxl>=3.1.0

# Tareas Programadas
APScheduler>=3.10.0

# Validación y Modelos
pydantic>=2.5.0

# Interfaz Gráfica
PyQt5>=5.15.0

# Utilidades
python-dateutil>=2.8.0
```

### 4️⃣ Crear Directorios Necesarios

```powershell
# Ejecutar como Administrador
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

### 5️⃣ Iniciar Servidor

```powershell
# Con el entorno virtual activado
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

---

## 👥 Sistema de Usuarios

### Tipos de Usuario

El sistema soporta 4 tipos de usuarios con diferentes niveles de acceso:

| Tipo | Descripción | Permisos |
|------|-------------|----------|
| **ADMIN** | Administrador del sistema | Acceso completo a todo el sistema |
| **FACTURACION** | Usuario de facturación electrónica | Acceso a módulos de facturación |
| **SOPORTE** | Técnico de soporte | Acceso a queries, manuales y tickets |
| **CLIENTE** | Cliente externo | Ver y editar tickets de su empresa |

### Endpoints de Autenticación

#### Login de Administrador
**POST** `/login-admin`
```json
{
  "username": "admin",
  "password": "contraseña"
}
```

#### Login de Soporte
**POST** `/login-soporte`
```json
{
  "username": "soporte1",
  "password": "contraseña"
}
```

#### Login de Cliente (NUEVO)
**POST** `/login-cliente`
```json
{
  "username": "cliente_empresa",
  "password": "contraseña"
}
```

**Response de Cliente:**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "usuario": {
    "id": 1,
    "username": "cliente_empresa",
    "tipo_usuario": "CLIENTE",
    "nombre_completo": "Juan Pérez",
    "empresa": {
      "id": 5,
      "rnc": "131793916",
      "razon_social": "Mi Empresa SRL"
    }
  },
  "permisos": {
    "tickets": {
      "ver": true,
      "crear": true,
      "editar": true,
      "eliminar": false
    },
    "queries": false,
    "manuales": false
  }
}
```

### Registro de Usuario
**POST** `/register`

#### Registro de Usuario de Facturación
```json
{
  "username": "usuario_factura",
  "password": "contraseña123",
  "tipo_usuario": "FACTURACION",
  "empresa_id": 5,
  "correo": "usuario@empresa.com",
  "nombre_completo": "Juan Pérez",
  "telefono": "809-555-1234",
  "cedula": "001-1234567-8",
  "direccion": "Santo Domingo",
  "puesto_trabajo": "Contador"
}
```

#### Registro de Usuario de Soporte
```json
{
  "username": "soporte_tech",
  "password": "contraseña123",
  "tipo_usuario": "SOPORTE",
  "empresa_id": 5,
  "nombre_completo": "María García"
}
```
> **Nota:** Para usuarios de soporte, `empresa_id` es opcional.

#### Registro de Usuario Cliente (NUEVO)
```json
{
  "username": "cliente_empresa",
  "password": "contraseña123",
  "tipo_usuario": "CLIENTE",
  "empresa_id": 5,
  "nombre_completo": "Carlos Rodríguez",
  "correo": "carlos@miempresa.com",
  "telefono": "809-555-5678"
}
```
> **Nota:** Para usuarios cliente, `empresa_id` es **obligatorio**.

---

## 🎫 Sistema de Tickets de Incidencias

### Permisos por Tipo de Usuario

| Acción | Admin | Soporte | Cliente |
|--------|-------|---------|---------|
| Ver todos los tickets | ✅ | ✅ | ❌ (solo de su empresa) |
| Crear tickets | ✅ | ✅ | ✅ |
| Editar tickets | ✅ | ✅ | ✅ (solo de su empresa) |
| Eliminar tickets | ✅ | ✅ | ❌ |
| Ver estadísticas | ✅ | ✅ | ✅ (de su empresa) |

### Filtrado Automático para Clientes

Cuando un usuario de tipo CLIENTE consulta la lista de tickets, el sistema automáticamente filtra por su empresa (RNC). No es necesario especificar el filtro manualmente.

### Endpoints de Tickets

#### Crear Ticket
**POST** `/api/tickets`

**Content-Type:** `multipart/form-data`

```
titulo: "Error en módulo de facturación"
prioridad: "ALTA"
categoria: "Sistema"
empresa: "131793916"
descripcion: "Descripción detallada del problema..."
creado_por: "cliente_empresa"
asignado_a: "soporte@empresa.com"
attachments: [archivos opcionales]
```

#### Listar Tickets
**GET** `/api/tickets?estado=PENDIENTE&limit=50`

> Para clientes, automáticamente se filtran solo los tickets de su empresa.

#### Obtener Detalle de Ticket
**GET** `/api/tickets/{ticket_id}`

> Retorna error 403 si el cliente intenta ver un ticket de otra empresa.

#### Actualizar Ticket
**PUT** `/api/tickets/{ticket_id}`
```json
{
  "estado": "EN_PROGRESO",
  "asignado_a": "soporte@empresa.com"
}
```

#### Eliminar Ticket
**DELETE** `/api/tickets/{ticket_id}`

> Los clientes reciben error 403 al intentar eliminar tickets.

### Prioridades y Estados

**Prioridades:**
- `BAJA` - Prioridad baja
- `MEDIA` - Prioridad media
- `ALTA` - Prioridad alta
- `CRITICA` - Prioridad crítica

**Estados:**
- `PENDIENTE` - Ticket nuevo
- `EN_PROGRESO` - En atención
- `RESUELTO` - Solución implementada
- `CERRADO` - Ticket cerrado

---

## 🏢 Estructura de Carpetas por Empresa

Cada empresa registrada obtiene automáticamente una estructura de carpetas basada en su RNC:

```
C:/Base/Ambiente/
├── PRD/{RNC}/
│   ├── Img/
│   ├── RI/
│   ├── Semillas/
│   │   ├── Firmadas/
│   │   └── Generadas/
│   ├── Bin/Servicios/Config/
│   ├── Token/
│   ├── XML/
│   │   ├── Firmadas/
│   │   └── Generadas/
│   ├── Cert/
│   └── CSV/
├── CERT/{RNC}/
└── QAS/{RNC}/
```

---

## 📝 Sistema de Queries SQL

Sistema para almacenar y gestionar queries SQL reutilizables.

### Endpoints

- **POST** `/api/queries` - Crear query
- **GET** `/api/queries` - Listar queries
- **GET** `/api/queries/{id}` - Obtener query
- **PUT** `/api/queries/{id}` - Actualizar query
- **DELETE** `/api/queries/{id}` - Eliminar query

### Tipos de Queries
- SELECT, UPDATE, INSERT, DELETE
- VIEW, PROCEDURE, FUNCTION, OTHER

---

## 📚 Sistema de Manuales PDF

Sistema para gestionar documentación en formato PDF.

### Endpoints

- **POST** `/api/manuales` - Subir manual (multipart/form-data)
- **GET** `/api/manuales` - Listar manuales
- **GET** `/api/manuales/{id}/download` - Descargar
- **GET** `/api/manuales/{id}/view` - Visualizar inline
- **DELETE** `/api/manuales/{id}` - Eliminar

### Categorías
- USUARIO, TECNICO, ADMINISTRADOR
- CONFIGURACION, API, OTRO

---

## 🔐 Autenticación y Seguridad

### JWT Tokens

Los endpoints protegidos requieren token JWT en el header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### API Keys

Algunos endpoints administrativos requieren API Key:

```
X-API-Key: tu_api_key_aqui
```

### Tiempos de Expiración

| Tipo de Usuario | Duración del Token |
|-----------------|-------------------|
| Admin | 1 hora (configurable) |
| Soporte | Variable |
| Cliente | 8 horas |

---

## 📡 Resumen de Endpoints

### Autenticación
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/login` | Login general |
| POST | `/login-admin` | Login de administrador |
| POST | `/login-soporte` | Login de soporte |
| POST | `/login-cliente` | Login de cliente |
| POST | `/register` | Registro de usuario |

### Tickets
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/tickets` | Crear ticket |
| GET | `/api/tickets` | Listar tickets |
| GET | `/api/tickets/{id}` | Detalle de ticket |
| PUT | `/api/tickets/{id}` | Actualizar ticket |
| DELETE | `/api/tickets/{id}` | Eliminar ticket |
| GET | `/api/tickets/stats` | Estadísticas |

### Queries SQL
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/queries` | Crear query |
| GET | `/api/queries` | Listar queries |
| GET | `/api/queries/{id}` | Obtener query |
| PUT | `/api/queries/{id}` | Actualizar query |
| DELETE | `/api/queries/{id}` | Eliminar query |

### Manuales
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/manuales` | Subir manual |
| GET | `/api/manuales` | Listar manuales |
| GET | `/api/manuales/{id}/download` | Descargar |
| DELETE | `/api/manuales/{id}` | Eliminar |

---

## 🛠️ Desarrollo

### Estructura del Proyecto

```
APIWEB/
├── run.py              # Punto de entrada
├── api.py              # Funciones de autenticación
├── routes.py           # Todos los endpoints
├── database.py         # Conexión a BD
├── ticket_models.py    # Modelos de tickets
├── query_models.py     # Modelos de queries
├── manual_models.py    # Modelos de manuales
├── requirements.txt    # Dependencias
├── config/
│   └── settings.json
├── data/
│   ├── apikey.json
│   └── configdgii.json
└── venv/               # Entorno virtual
```

### Ejecutar en Desarrollo

```powershell
# Activar entorno virtual
.\venv\Scripts\activate

# Ejecutar servidor
python run.py
```

El servidor estará disponible en: `https://localhost:8001`

---

## 📄 Licencia

Sistema propietario de ASESYS SRL.

---

**Última actualización:** Enero 2026
