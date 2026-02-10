import traceback
import pyodbc

# Lista los drivers disponibles
drivers = [x for x in pyodbc.drivers()]
print("Drivers disponibles:", drivers)

# Intenta conectar con el primer driver para SQL Server que encuentres
for driver in drivers:
    if "SQL Server" in driver:
        try:
            conn_str = f"DRIVER={{{driver}}};SERVER=192.168.1.128;DATABASE=lhfe;UID=sistema;PWD=@@sistema"
            conn = pyodbc.connect(conn_str)
            print(f"Conexión exitosa usando: {driver}")
            conn.close()
        except Exception as e:
            print(f"Error con driver {driver}: {e}")
