# Scripts de creación de tablas (SQL Server)

- `01_create_tables.sql`: DDL para crear `dbo.FEEncabezado` (PK ENCF) y `dbo.FEDetalle` (PK compuesta ENCF, NumeroLinea) con FK.
- `run_ddl_windows.bat`: ejemplo para ejecutar el DDL con `sqlcmd` en Windows (edita SERVER/DB/USER/PASS).
- `run_ddl_linux_mac.sh`: ejemplo para Linux/Mac con `sqlcmd` (requiere mssql-tools).

> Alternativa: también puedes indicar este DDL directamente en la GUI (campo **DDL**) y se ejecuta automáticamente antes de cargar.
