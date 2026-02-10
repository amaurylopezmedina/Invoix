#!/usr/bin/env bash
# Ejecuta el DDL contra SQL Server usando sqlcmd (msodbc + mssql-tools instalados).
# Edita los parámetros según tu entorno.
SERVER="localhost"
DB="DBNAME"
USER="sa"
PASS="YourStrong!Passw0rd"
DDL="01_create_tables.sql"

/opt/mssql-tools/bin/sqlcmd -S "$SERVER" -d "$DB" -U "$USER" -P "$PASS" -i "$DDL"
