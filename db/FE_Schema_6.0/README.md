# FE Schema Project (Completo)

Incluye:
- JSON por tablas (`tables/*.table.json`)
- JSON por vistas (`views/*.view.json`)
- Motor de instalación con:
  - Comparador inteligente vs `sys.columns`
  - Auditoría de cambios en `dbo.SchemaAudit`
  - Creación automática de base de datos si no existe
  - Dry-Run (simulación)
  - Validación de JSON

## Ejecutar UI
```bash
python -m ui.main_ui
```

## Ejecutar por CLI
```bash
python -c "import schema_manager; schema_manager.run_install('DEV', dry_run=False)"
```

## Auditoría
Los cambios quedan registrados en:
- `dbo.SchemaAudit`


## Nota
Los archivos cn_dev.ini, cn_cert.ini y cn_prd.ini están en la carpeta **config/**.


### SchemaAudit (versionado + usuario/host/app)
- run_id (UUID por ejecución)
- schema_version (int del paquete)
- sql_user (ORIGINAL_LOGIN())
- host_name (HOST_NAME())
- app_name (PROGRAM_NAME())

## Rollback automático (C - mixto con prompt)
- Snapshots por versión en carpeta `snapshots/`.
- Ventana de rollback con confirmación extra cuando el modo NO es sólo estructura.
- El modo `mixed` requiere confirmación explícita antes de ejecutar cualquier operación que pueda afectar datos.

## Export Live (SQL → JSON)
- Herramienta en `tools/export_schema.py` que exporta el esquema actual de SQL Server a JSON compatible con el gestor.
- Ideal para tomar producción y replegarla en DEV/CERT.
