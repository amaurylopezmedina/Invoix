from db.uDB import ConectarDB


def ensure_table(nombre_tabla, campos, esquema="dbo"):
    """
    Crea una tabla si no existe, o agrega los campos que falten si ya existe.

    :param nombre_tabla: str, nombre de la tabla
    :param campos: dict, {nombre_campo: definicion_sql}
    :param esquema: str, nombre del esquema SQL (por defecto 'dbo')
    """
    cn1 = ConectarDB()

    try:
        # Crear tabla si no existe
        campos_sql = ", ".join([f"{k} {v}" for k, v in campos.items()])
        query_create = f"""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{nombre_tabla}' AND xtype='U')
        BEGIN
            CREATE TABLE {esquema}.{nombre_tabla} ({campos_sql})
        END
        """
        cn1.execute_query(query_create)

        # Agregar campos que no existan usando SQL condicional
        for campo, definicion in campos.items():
            # Usar una consulta condicional que verifica si la columna existe antes de agregarla
            query_alter = f"""
            IF NOT EXISTS (
                SELECT * FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = '{nombre_tabla}' 
                AND TABLE_SCHEMA = '{esquema}' 
                AND COLUMN_NAME = '{campo}'
            )
            BEGIN
                ALTER TABLE {esquema}.{nombre_tabla} ADD {campo} {definicion}
            END
            """
            try:
                cn1.execute_query(query_alter)
                print(f"Campo '{campo}' procesado para la tabla '{nombre_tabla}'.")
            except Exception as e:
                print(f"[ensure_table] Error procesando campo '{campo}': {e}")

        print(f"Tabla '{nombre_tabla}' asegurada y actualizada correctamente.")

    except Exception as e:
        print(
            f"[ensure_table] Error general al asegurar la tabla '{nombre_tabla}': {e}"
        )
    finally:
        # Asegurar que la conexión se cierre
        try:
            cn1.close()
        except:
            pass


def registrar_actividad_log(
    rnc_emisor, encf, tipo_actividad, fecha_actividad, equipo, ruta_impresion, impresora
):
    """
    Inserta un registro en la tabla LogActividadesFE.
    """
    try:
        from datetime import datetime  # Aseguramos la importación

        cn1 = ConectarDB()

        # Protección: si es None, usar ahora
        if fecha_actividad is None:
            fecha_actividad = datetime.now()

        # Si es datetime, convertir a string
        if isinstance(fecha_actividad, datetime):
            fecha_actividad_str = fecha_actividad.strftime("%Y-%m-%d %H:%M:%S")
        else:
            # Asegurar que sea string y no None
            fecha_actividad_str = (
                str(fecha_actividad)
                if fecha_actividad is not None
                else datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

        # Usar parámetros nombrados (que es lo que funciona)
        named_params = {
            "rnc_emisor": str(rnc_emisor) if rnc_emisor is not None else "",
            "encf": str(encf) if encf is not None else "",
            "tipo_actividad": str(tipo_actividad) if tipo_actividad is not None else "",
            "fecha_actividad": fecha_actividad_str,
            "equipo": str(equipo) if equipo is not None else "",
            "ruta_impresion": str(ruta_impresion) if ruta_impresion is not None else "",
            "impresora": str(impresora) if impresora is not None else "",
        }

        # Query con parámetros nombrados
        named_query = (
            "INSERT INTO LogActividadesFE (RncEmisor, encf, TipoActividad, FechaActividad, Equipo, RutaImpresion, impresora) "
            "VALUES (:rnc_emisor, :encf, :tipo_actividad, :fecha_actividad, :equipo, :ruta_impresion, :impresora)"
        )

        cn1.execute_query(named_query, named_params)
        print("Actividad registrada en LogActividadesFE.")

    except Exception as e:
        print(f"Error al registrar actividad en LogActividadesFE: {e}")
        print(
            f"Parámetros: rnc_emisor={rnc_emisor}, encf={encf}, tipo_actividad={tipo_actividad}, "
            f"fecha_actividad={fecha_actividad}, equipo={equipo}, ruta_impresion={ruta_impresion}, impresora={impresora}"
        )
