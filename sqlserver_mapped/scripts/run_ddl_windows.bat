@echo off
REM Ejecuta el DDL contra SQL Server usando sqlcmd.
REM Edita los parámetros SERVER, DB, USER, PASS o usa Trusted_Connection.

set SERVER=localhost
set DB=DBNAME
set USER=sa
set PASS=YourStrong!Passw0rd
set DDL=01_create_tables.sql

REM Ejemplo Trusted Connection (comenta/descomenta según tu caso)
REM sqlcmd -S %SERVER% -d %DB% -E -i %DDL%

REM Usuario/Password
sqlcmd -S %SERVER% -d %DB% -U %USER% -P %PASS% -i %DDL%
pause
