# Monitor de Facturación Electrónica - API REST

API simplificada para monitorear estados fiscales de comprobantes electrónicos sin autenticación. Diseñada para ejecutarse en aplicaciones de escritorio.

## Configuración

La API se conecta a la base de datos usando el archivo `config/CN.ini` en la raíz del proyecto.

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecución

```bash
python run.py
```

El servidor se iniciará en `https://0.0.0.0:8001`

## Endpoints

### 1. Obtener Estados Fiscales

**GET** `/estados-fiscales`

Consulta los comprobantes electrónicos con filtros opcionales.

**Parámetros obligatorios:**
- `fecha_inicio`: Fecha de inicio (formato: YYYY-MM-DD)
- `fecha_fin`: Fecha de fin (formato: YYYY-MM-DD)

**Parámetros opcionales:**
- `caja`: Filtro por caja (default: TODAS)
- `estado_fiscal`: Filtro por estado fiscal (default: TODOS)
- `rncemisor`: Filtro por RNC emisor (default: TODOS)
- `tipo_ecf`: Filtro por tipo de eCF (default: TODOS)
- `order_field`: Campo de ordenamiento - FechaEmision o Factura (default: FechaEmision)
- `order_dir`: Dirección de ordenamiento - ASC o DESC (default: DESC)

**Ejemplo:**
```
GET /estados-fiscales?fecha_inicio=2025-01-01&fecha_fin=2025-01-31&estado_fiscal=2
```

**Respuesta:**
```json
{
  "resultados": [
    {
      "tipo_venta": "CONTADO",
      "factura": "001234",
      "tipo_ecf": "31",
      "encf": "E310000000001",
      "estado_fiscal": 2,
      "descripcion_estado_fiscal": "ACEPTADO",
      "urlc": "https://...",
      "resultado_estado_fiscal": "APROBADO",
      "monto_facturado": "1,500.00",
      "itbis_facturado": "270.00",
      "monto_dgii": "1,500.00",
      "monto_itbis_dgii": "270.00"
    }
  ]
}
```

### 2. Actualizar Estado Fiscal

**PUT/POST** `/actualizar-estado-fiscal`

Actualiza el estado fiscal de un comprobante a anulado (estado 4).

**Parámetros obligatorios:**
- `rnc`: RNC del emisor
- `ncf`: Número de comprobante fiscal (eNCF)

**Ejemplo:**
```
PUT /actualizar-estado-fiscal?rnc=123456789&ncf=E310000000001
```

**Respuesta:**
```json
{
  "mensaje": "Actualización exitosa",
  "rnc": "123456789",
  "ncf": "E310000000001"
}
```

### 3. Health Check

**GET** `/health`

Verifica que el servicio está activo.

**Respuesta:**
```json
{
  "status": "ok",
  "service": "Monitor API"
}
```

## Notas

- No requiere autenticación
- Usa el archivo `CN.ini` para la conexión a la base de datos
- Los registros de log se muestran en la consola
- Diseñado para aplicaciones desktop que necesitan consultar estados fiscales
