import logging
import os
import shutil
from datetime import datetime, timedelta


def clean_old_logs(days=3):
    """
    Elimina logs que tengan más de 'days' días de antigüedad.
    Por defecto elimina logs de más de 3 días.

    :param days: Número de días para considerar un log como antiguo
    """
    try:
        log_base_dir = "log_generales"
        if not os.path.exists(log_base_dir):
            return

        cutoff_date = datetime.now() - timedelta(days=days)

        for root, dirs, files in os.walk(log_base_dir):
            # Buscar directorios con formato de fecha (YYYY-MM-DD)
            for dir_name in dirs[
                :
            ]:  # Usar slice para evitar problemas al modificar durante iteración
                try:
                    # Verificar si el nombre del directorio es una fecha válida
                    dir_date = datetime.strptime(dir_name, "%Y-%m-%d")

                    # Si la fecha es anterior al cutoff, eliminar el directorio
                    if dir_date < cutoff_date:
                        dir_path = os.path.join(root, dir_name)
                        print(f"Eliminando directorio de logs antiguo: {dir_path}")
                        shutil.rmtree(dir_path)
                        dirs.remove(
                            dir_name
                        )  # Remover de la lista para evitar procesarlo
                except ValueError:
                    # Si no es una fecha válida, continuar con el siguiente directorio
                    continue
                except Exception as e:
                    print(f"Error al eliminar directorio {dir_name}: {e}")

        print(
            f"Limpieza de logs completada. Eliminados logs anteriores a {cutoff_date.strftime('%Y-%m-%d')}"
        )

    except Exception as e:
        print(f"Error durante la limpieza de logs: {e}")


def setup_general_handler():
    """
    Crea un FileHandler que escribe logs generales diarios.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    log_dir = os.path.join("log_generales", "log_diario", today)
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"log_{today}.log")

    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    return file_handler


def setup_logger(
    log_folder, enable_general=True, enable_individual=True, auto_cleanup=True
):
    """
    Crea y configura un logger para un modulo especifico.
    Guarda los logs en 'log_generales/<log_folder>/<YYYY-MM-DD>/log.log'.
    Tambien puede propagar los mensajes al logger general del sistema.

    :param log_folder: Nombre del módulo o carpeta.
    :param enable_general: Si True, agrega handler de log general.
    :param enable_individual: Si True, guarda log individual del módulo.
    :param auto_cleanup: Si True, ejecuta limpieza automática de logs antiguos.
    """
    try:
        # Ejecutar limpieza automática si está habilitada
        if auto_cleanup:
            clean_old_logs()

        today = datetime.now().strftime("%Y-%m-%d")
        logger_name = f"AppLogger_{log_folder}_{today}"
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

            if enable_individual:
                log_dir = os.path.join("log_generales", log_folder, today)
                os.makedirs(log_dir, exist_ok=True)
                log_path = os.path.join(log_dir, "log.log")
                file_handler = logging.FileHandler(log_path)
                file_handler.setLevel(logging.INFO)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)

            if enable_general:
                general_handler = setup_general_handler()
                logger.addHandler(general_handler)

            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        return logger
    except Exception as e:
        print(f"Error al configurar el logger: {e}")
        raise


def log_event(logger, level, message):
    """
    Registra un evento en el logger del modulo (propagando al general si está configurado).
    """
    try:
        level = level.lower()
        log_func = getattr(logger, level, logger.info)
        log_func(message)
    except Exception as e:
        print(f"Error al registrar el evento: {e}")


def force_cleanup_logs(days=3):
    """
    Función de limpieza forzada que puede ser llamada manualmente.

    :param days: Número de días para considerar un log como antiguo (por defecto 3)
    """
    print(f"Iniciando limpieza manual de logs antiguos (>{days} días)...")
    clean_old_logs(days)


if __name__ == "__main__":
    logger = setup_logger("modulo_api", enable_general=True, enable_individual=True)

    log_event(logger, "info", "Inicio del servicio API.")
    log_event(logger, "debug", "Este es un mensaje de depuracion.")
    log_event(logger, "error", "Error durante la ejecucion del proceso.")
    log_event(logger, "warning", "Advertencia de uso de recurso obsoleto.")
    log_event(logger, "critical", "Fallo critico del sistema.")

    # Ejemplo de limpieza manual de logs
    # force_cleanup_logs(3)  # Descomenta para ejecutar limpieza manual
