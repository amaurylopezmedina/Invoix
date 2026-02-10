import inspect
import os
import sys
import time
import traceback
from collections import defaultdict
from typing import Dict, List

import portalocker
import pyodbc

from config.uGlobalConfig import GConfig
from db.uDB import ConectarDB
from glib.dgii_health_checker import ErrorType, ServiceStatus, get_health_checker
from glib.log_g import setup_logger
from glib.Servicios import UnlockCK
from glib.ufe import EnvioDGII
from glib.uGlobalLib import load_interval_config, mostrarConfiguracion

if __name__ == "__main__":
    """
    Programa principal para envío de facturas electrónicas a ASESYS.
    Verifica bloqueo de instancia, conecta a BD y procesa facturas pendientes.
    """
    logger = setup_logger("FEEnvioASESYS.log")
    # Evitar que el programa se ejecute más de una vez
    lock_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "FEImpresionASESYS.lock"
    )

    # Abrir el archivo para bloqueo
    lock_file = open(lock_file_path, "w")
    try:
        # Intentar bloquear el archivo de forma exclusiva y no bloqueante
        portalocker.lock(lock_file, portalocker.LOCK_EX | portalocker.LOCK_NB)

        # Si llegamos aquí, tenemos el bloqueo
        # Escribir el PID para identificación
        lock_file.write(f"{os.getpid()}")
        lock_file.flush()
    except portalocker.LockException:
        print("¡Ya hay otra instancia del programa en ejecución!")
        sys.exit(1)

    try:
        UnlockCK()
        GConfig.cargar(1)

        # Conexión a la base de datos
        cn1 = ConectarDB()
        frame = inspect.currentframe()
        archivo = frame.f_code.co_filename
        mostrarConfiguracion(GConfig, cn1, archivo)

        IConfig = load_interval_config()
        check_interval: int = IConfig.get("check_interval_envio", 5)
        logger.info(f"Intervalo de chequeo configurado: {check_interval} segundos")

        # Obtener instancia del health checker
        health_checker = get_health_checker()

        # Contadores para métricas y tiempos adaptativos
        error_count = 0
        max_consecutive_errors = 10
        check_service_interval = 60  # Cada 1 minuto verificar servicio (más reactivo)
        last_service_check = 0
        current_backoff = 1  # Para backoff exponencial en errores recuperables

        # Cache de tokens por RNC para reducir consultas a BD
        token_cache: Dict[str, tuple] = {}  # {RNC: (token, expiry_time)}

        # Configuración de batch processing
        BATCH_SIZE = 50  # Procesar en lotes de 50 facturas
        BATCH_COMMIT_INTERVAL = 10  # Commit cada 10 facturas para balance

        while True:
            try:
                # Verificación periódica del estado de servicios DGII
                current_time = time.time()
                if current_time - last_service_check > check_service_interval:
                    service_status = health_checker.check_service_health(
                        force_check=True
                    )
                    logger.info(
                        f"📊 Verificación periódica - Estado servicios DGII: {service_status.value}"
                    )
                    last_service_check = current_time

                    # Si el servicio está en mantenimiento, esperar tiempo razonable
                    if service_status == ServiceStatus.MAINTENANCE:
                        wait_time = min(check_interval * 12, 60)  # Máx 60s
                        logger.warning(
                            f"⏸ DGII EN MANTENIMIENTO PROGRAMADO\n"
                            f"   → El servicio se pausará por {wait_time}s\n"
                            f"   → Las facturas pendientes se procesarán automáticamente cuando DGII esté disponible\n"
                            f"   → No se requiere intervención manual"
                        )
                        time.sleep(wait_time)
                        continue

                    elif service_status == ServiceStatus.UNAVAILABLE:
                        wait_time = min(check_interval * 6, 30)  # Máx 30s, más ágil
                        logger.warning(
                            f"⚠ DGII NO DISPONIBLE (timeout/error de red)\n"
                            f"   → Esperando {wait_time}s antes de reintentar\n"
                            f"   → El servicio continuará automáticamente cuando DGII responda"
                        )
                        time.sleep(wait_time)
                        continue

                    elif service_status == ServiceStatus.DEGRADED:
                        logger.warning(
                            "🐌 DGII CON RESPUESTA LENTA (servicio degradado)\n"
                            "   → Continuando procesamiento con precaución\n"
                            "   → Se aplicará backoff en caso de errores"
                        )

                # Usar READ UNCOMMITTED para menos bloqueos y mejor rendimiento
                # Esto es seguro porque solo leemos facturas pendientes (EstadoFiscal=3)
                cursor = cn1.connection.cursor()
                cursor.execute("SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED;")
                cursor.execute("SET LOCK_TIMEOUT 2000;")  # Reducido a 2s

                # Query optimizado: TOP reducido, índice hint, columnas específicas
                # NOTA: Crear índice: CREATE INDEX IX_FEEncabezado_EstadoFiscal_Envio
                # ON [tabla] (EstadoFiscal, TipoECFL, FechaEmision) INCLUDE (RNCEmisor, eNCF)
                query = f"""
                    SELECT TOP {BATCH_SIZE}
                        RNCEmisor, eNCF, Tabla, campo1, campo2, TipoECF, 
                        MontoTotal, CodigoSeguridad, EstadoFiscal, TipoECFL,
                        RazonSocialEmisor, RazonSocialComprador, FechaCreacion
                    FROM vFEEncabezado WITH (READUNCOMMITTED, INDEX(IX_FEEncabezado_EstadoFiscal_Envio))
                    WHERE EstadoFiscal = 3
                    AND TipoECFL = 'E'
                    AND FechaEmision < DATEADD(DAY, 1, CAST(GETDATE() AS DATE))
                    ORDER BY FechaCreacion
                """

                cursor.execute(query)
                rows = cursor.fetchall()  # Fetch all batch at once
                cursor.close()

                procesados: int = 0
                errores_recuperables: int = 0
                errores_por_rnc: Dict[str, int] = defaultdict(int)

                # Procesar batch completo
                for idx, row in enumerate(rows, 1):
                    try:
                        EnvioDGII(cn1, row, token_cache=token_cache)
                        procesados += 1
                        error_count = 0  # Reset contador de errores consecutivos
                        current_backoff = 1  # Reset backoff tras éxito

                        # Commit periódico (cada N facturas) para mejor performance
                        if procesados % BATCH_COMMIT_INTERVAL == 0:
                            try:
                                cn1.connection.commit()
                            except:
                                pass

                        # Pausa adaptativa: más rápida al inicio, más lenta si hay errores
                        pause = 0.02 if errores_recuperables == 0 else 0.1
                        time.sleep(pause)

                    except Exception as e:
                        # Clasificar el error
                        error_type = health_checker.classify_error(e)

                        if error_type in [
                            ErrorType.NETWORK,
                            ErrorType.TIMEOUT,
                            ErrorType.SERVER_ERROR,
                            ErrorType.MAINTENANCE,
                        ]:
                            # Error recuperable - no terminar el programa
                            errores_recuperables += 1
                            errores_por_rnc[row.RNCEmisor] += 1

                            # Si un RNC específico tiene muchos errores, saltar al siguiente
                            if errores_por_rnc[row.RNCEmisor] >= 5:
                                logger.warning(
                                    f"RNC {row.RNCEmisor}: {errores_por_rnc[row.RNCEmisor]} errores. "
                                    "Saltando temporalmente este emisor."
                                )
                                continue

                            # Mensaje específico según tipo de error
                            if error_type == ErrorType.MAINTENANCE:
                                logger.warning(
                                    f"⏸ NCF {row.eNCF}: DGII en mantenimiento. "
                                    f"Se reintentará automáticamente cuando esté disponible."
                                )
                            elif error_type == ErrorType.TIMEOUT:
                                logger.warning(
                                    f"⏱ NCF {row.eNCF}: Timeout - DGII no respondió a tiempo. "
                                    f"Se reintentará en el próximo ciclo."
                                )
                            elif error_type == ErrorType.NETWORK:
                                logger.warning(
                                    f"🌐 NCF {row.eNCF}: Error de red/conectividad. "
                                    f"Se reintentará en el próximo ciclo."
                                )
                            else:
                                logger.warning(
                                    f"🔄 NCF {row.eNCF}: Error recuperable ({error_type.value}). "
                                    f"Se reintentará en el próximo ciclo."
                                )

                            # Si hay muchos errores recuperables seguidos (20% del batch), esperar más
                            if errores_recuperables >= max(3, len(rows) * 0.2):
                                logger.warning(
                                    f"{errores_recuperables} errores recuperables consecutivos. "
                                    "Verificando estado del servicio..."
                                )
                                service_status = health_checker.check_service_health(
                                    force_check=True
                                )

                                # Manejo específico según estado del servicio
                                if service_status == ServiceStatus.MAINTENANCE:
                                    wait_time = min(check_interval * 12, 60)  # Máx 60s
                                    logger.warning(
                                        f"⏸ DGII en MANTENIMIENTO. Sistema pausado por {wait_time}s. "
                                        "Las facturas se procesarán cuando el servicio esté disponible."
                                    )
                                    time.sleep(wait_time)
                                    break  # Salir y reintentar en próximo ciclo

                                elif service_status == ServiceStatus.UNAVAILABLE:
                                    wait_time = min(check_interval * 6, 30)  # Máx 30s
                                    logger.warning(
                                        f"⚠ DGII NO DISPONIBLE. Esperando {wait_time}s antes de reintentar..."
                                    )
                                    time.sleep(wait_time)
                                    break  # Salir y reintentar

                                elif service_status == ServiceStatus.DEGRADED:
                                    wait_time = min(
                                        check_interval * 3, 15
                                    )  # Máx 15s, más ágil
                                    logger.warning(
                                        "🐌 DGII DEGRADADO. Reduciendo velocidad de procesamiento..."
                                    )
                                    time.sleep(wait_time)
                                    # Continuar procesando pero más lento

                                else:
                                    # UNKNOWN o problema temporal - backoff progresivo
                                    wait_time = min(
                                        check_interval * current_backoff, 20
                                    )
                                    logger.warning(
                                        f"Servicio DGII {service_status.value}. "
                                        f"Pausando {wait_time}s antes de continuar..."
                                    )
                                    current_backoff = min(
                                        current_backoff * 2, 4
                                    )  # Backoff exponencial hasta 4x
                                    time.sleep(wait_time)
                                    break
                        else:
                            # Error no recuperable - ya fue manejado en EnvioDGII
                            logger.error(
                                f"Error no recuperable procesando NCF {row.eNCF}: "
                                f"{error_type.value}"
                            )

                # Commit final del batch
                try:
                    cn1.connection.commit()
                except Exception as commit_error:
                    logger.warning(f"Error en commit final: {commit_error}")

                # Logging de métricas
                if procesados > 0 or errores_recuperables > 0:
                    if errores_recuperables == 0:
                        logger.info(
                            f"✅ Ciclo completado exitosamente: {procesados} facturas procesadas"
                        )
                    else:
                        logger.info(
                            f"📊 Ciclo completado: {procesados} procesadas, "
                            f"{errores_recuperables} pendientes de reintento (error recuperable)"
                        )

                # Limpiar cache de tokens viejos (cada ciclo)
                current_ts = time.time()
                token_cache = {
                    k: v for k, v in token_cache.items() if v[1] > current_ts
                }

                # Nada para procesar → descansar
                if len(rows) == 0:
                    time.sleep(check_interval)
                elif errores_recuperables > 0:
                    # Hubo errores recuperables, usar backoff progresivo
                    wait_time = min(check_interval * current_backoff, 20)
                    logger.info(
                        f"⏳ Esperando {wait_time}s antes del próximo ciclo "
                        f"({errores_recuperables} facturas pendientes de reintento)"
                    )
                    current_backoff = min(
                        current_backoff * 1.5, 4
                    )  # Backoff progresivo
                    time.sleep(wait_time)
                else:
                    # Procesamiento exitoso sin errores - pequeña pausa
                    time.sleep(0.5)

            except pyodbc.Error as db_error:
                # Errores de base de datos - no terminar el programa
                error_count += 1
                logger.error(
                    f"Error de base de datos (intento {error_count}): {db_error}"
                )

                if error_count >= max_consecutive_errors:
                    logger.critical(
                        f"Máximo de errores consecutivos alcanzado ({max_consecutive_errors}). "
                        "Terminando servicio."
                    )
                    sys.exit(1)

                # Esperar antes de reintentar BD - backoff progresivo
                wait_time = min(check_interval * min(error_count, 3), 15)  # Máx 15s
                time.sleep(wait_time)

                # Intentar reconectar a BD
                try:
                    cn1 = ConectarDB()
                    logger.info("Reconexión a BD exitosa")
                    error_count = 0
                except Exception as reconn_error:
                    logger.error(f"Error reconectando a BD: {reconn_error}")

            except KeyboardInterrupt:
                logger.info("Interrupción manual del servicio")
                sys.exit(0)

            except Exception as e:
                # Otros errores inesperados
                error_count += 1
                logger.error(
                    f"Error inesperado en bucle principal (intento {error_count}): {e}:"
                    f"{traceback.extract_tb(sys.exc_info()[2])}"
                )

                if error_count >= max_consecutive_errors:
                    logger.critical(
                        f"Máximo de errores consecutivos alcanzado ({max_consecutive_errors}). "
                        "Terminando servicio."
                    )
                    sys.exit(1)

                # Backoff progresivo para errores inesperados
                wait_time = min(check_interval * min(error_count, 2), 10)  # Máx 10s
                time.sleep(wait_time)

    finally:
        lock_file.close()
