
import datetime

def templates():
    return {
        "TABLE": {
            "schema": "dbo",
            "table": "NuevaTabla",
            "description": "Descripción de la tabla (no afecta DDL)",
            "fields": {
                "Id": {
                    "type": "int",
                    "nullable": False,
                    "identity": True,
                    "description": "Clave primaria"
                }
            }
        },
        "VIEW": {
            "type": "view",
            "schema": "dbo",
            "name": "NuevaVista",
            "execution": "replace",
            "description": "Descripción de la vista (no afecta DDL)",
            "ddl": "CREATE VIEW dbo.NuevaVista AS SELECT 1 AS X;"
        },
        "PROC": {
            "type": "proc",
            "schema": "dbo",
            "name": "NuevoSP",
            "execution": "replace",
            "description": "Descripción del procedimiento (no afecta DDL)",
            "ddl": "CREATE OR ALTER PROCEDURE dbo.NuevoSP AS SELECT 1;"
        }
    }
