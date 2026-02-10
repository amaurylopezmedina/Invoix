# Proyecto DGII SQLAlchemy — v5.0

## NUEVO en v5.0
1) **Auditoría / Bitácora**
   - Registra acciones (ejecución de SP, importaciones, sincronizaciones, ediciones, pruebas de conexión, etc.) en SQLite (`data/procedimientos.db`, tabla `Bitacora`).
   - Pantalla **Visor de Bitácora** con filtros, scroll horizontal, y exportación a TXT.
2) **CLI** (`src/cli.py`)
   - `test-conn` — probar conexión.
   - `exec-sp` — ejecutar cualquier SP con parámetros y exportar a CSV o XLSX (xlsxwriter).
   - `import-procs` — importar uno o todos los procedimientos desde SQL Server a SQLite.
   - `sync-procs` — `--dry-run` (NOEXEC) o `--apply` para aplicar (correr scripts en el servidor).
   - `list-procs` / `list-views` — listar objetos del servidor.
3) **Perfiles múltiples de conexión**
   - Archivo `config/profiles.json` (opcional) con varios perfiles. Campo `"default"` para predeterminado.
   - Pantalla **Gestor de Perfiles** (agregar, editar, eliminar, probar, marcar por defecto).
   - Compatibilidad retro con `config/CNDB.json` como perfil único si no existe `profiles.json`.

## Estructura
- `src/main_app.py` — Menú principal (añadidos: Perfiles y Bitácora).
- `src/common_config.py` — Carga de perfiles y construcción de conexión.
- `src/common_audit.py` — Utilidad de auditoría (SQLite).
- `src/pantalla_configuracion_bd.py` — Editor rápido de `CNDB.json` (se mantiene).
- `src/gestor_perfiles_bd.py` — Gestor de múltiples perfiles (`profiles.json`).
- `src/pantalla_facturas_ecf.py` — Ejecución de SPs (contado/crédito), ahora con auditoría y copia de SQL.
- `src/gestor_procedimientos_sql.py` — Gestor de Procedimientos (con audit + backup + diff + dry-run).
- `src/gestor_vistas_sql.py` — Gestor de Vistas (con audit + backup + diff + dry-run).
- `src/visor_bitacora.py` — Visor de bitácora/auditoría.
- `src/cli.py` — CLI sin pandas.
- `config/CNDB.json` — Perfil rápido por defecto.
- `config/profiles.json` — Varios perfiles (opcional, se crea al guardar desde gestor de perfiles).
- `data/procedimientos.db` — SQLite (procedimientos, vistas, historial y bitácora).
- `backups/` — Respaldos de código en servidor.

## Ejecutar GUI
```bash
pip install -r requirements.txt
python src/main_app.py
```

## Usar la CLI
```bash
# Probar conexión (perfil por defecto o CNDB.json)
python src/cli.py test-conn [--profile PERFIL]

# Ejecutar SP y exportar
python src/cli.py exec-sp --sp dbo.sp_FEVentaContadoRD --rnc 131709745 --desde 2025-10-01 --hasta 2025-10-31 --out resultados.xlsx

# Importar TODOS los procedimientos a SQLite
python src/cli.py import-procs --all

# Simular sincronización (dry-run)
python src/cli.py sync-procs --dry-run

# Listar objetos
python src/cli.py list-procs
python src/cli.py list-views
```