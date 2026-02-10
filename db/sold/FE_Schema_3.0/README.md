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
