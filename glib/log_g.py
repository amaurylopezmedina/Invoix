"""
Módulo de logging general para la aplicación.

Proporciona funciones para configurar loggers, limpiar logs antiguos
y registrar eventos.
"""

import logging
import os
import shutil
import sys
from datetime import datetime, timedelta

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(project_root)


def clean_old_logs(days: int = 3) -> None:
    """
    Elimina logs que tengan más de 'days' días de antigüedad.
    Por defecto elimina logs de más de 3 días.

    Args:
        days: Número de días para considerar un log como antiguo
    """
    try:
        log_base_dir = "log_generales"
        if not os.path.exists(log_base_dir):
            return

        cutoff_date = datetime.now() - timedelta(days=days)

        for root, dirs, _ in os.walk(log_base_dir):
            # Buscar directorios con formato de fecha (YYYY-MM-DD)
            for dir_name in dirs[
                :
            ]:  # Usar slice para evitar modificar lista durante iteración
                try:
                    # Verificar si el nombre del directorio es una fecha válida
                    dir_date = datetime.strptime(dir_name, "%Y-%m-%d")

                    # Si la fecha es anterior al cutoff, eliminar el directorio
                    if dir_date < cutoff_date:
                        dir_path = os.path.join(root, dir_name)
                        print("Eliminando directorio de logs antiguo:", dir_path)
                        shutil.rmtree(dir_path)
                        dirs.remove(
                            dir_name
                        )  # Remover de la lista para evitar procesarlo
                except ValueError:
                    # Si no es una fecha válida, continuar con el siguiente
                    # directorio
                    continue
                except OSError as e:
                    print(f"Error al eliminar directorio {dir_name}: {e}")

        print(
            f"Limpieza de logs completada. Eliminados logs anteriores a "
            f"{cutoff_date.strftime('%Y-%m-%d')}"
        )

    except OSError as e:
        print(f"Error durante la limpieza de logs: {e}")


def setup_general_handler() -> logging.Handler:
    """
    Crea un FileHandler que escribe logs generales diarios.

    Returns:
        logging.Handler: El handler configurado para logs generales.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    log_dir = os.path.join("log_generales", "log_diario", today)
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"log_{today}.log")

    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    return file_handler


def setup_logger(
    log_folder: str,
    enable_general: bool = True,
    enable_individual: bool = True,
    auto_cleanup: bool = True,
) -> logging.Logger:
    """
    Crea y configura un logger para un modulo especifico.
    Guarda los logs en 'log_generales/<log_folder>/<YYYY-MM-DD>/log.log'.
    Tambien puede propagar los mensajes al logger general del sistema.

    Args:
        log_folder: Nombre del módulo o carpeta.
        enable_general: Si True, agrega handler de log general.
        enable_individual: Si True, guarda log individual del módulo.
        auto_cleanup: Si True, ejecuta limpieza automática de logs antiguos.

    Returns:
        logging.Logger: El logger configurado.
    """
    try:
        # Ejecutar limpieza automática si está habilitada
        if auto_cleanup:
            clean_old_logs()

        today = datetime.now().strftime("%Y-%m-%d")
        logger_name = f"AppLogger_{log_folder}_{today}"
        logger_instance = logging.getLogger(logger_name)
        logger_instance.setLevel(logging.INFO)

        if not logger_instance.handlers:
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

            if enable_individual:
                log_dir = os.path.join("log_generales", log_folder, today)
                os.makedirs(log_dir, exist_ok=True)
                log_path = os.path.join(log_dir, "log.log")
                file_handler = logging.FileHandler(log_path, encoding='utf-8')
                file_handler.setLevel(logging.INFO)
                file_handler.setFormatter(formatter)
                logger_instance.addHandler(file_handler)

            if enable_general:
                general_handler = setup_general_handler()
                logger_instance.addHandler(general_handler)

            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(formatter)
            logger_instance.addHandler(console_handler)

        return logger_instance
    except Exception as e:
        print(f"Error al configurar el logger: {e}")
        raise


def log_event(log_instance: logging.Logger, level: str, message: str) -> None:
    """
    Registra un evento en el logger del modulo (propagando al general
    si está configurado).

    Args:
        log_instance: Instancia del logger.
        level: Nivel del log (info, debug, error, etc.).
        message: Mensaje a registrar.
    """
    try:
        level = level.lower()
        log_func = getattr(log_instance, level, log_instance.info)
        log_func(message)
    except AttributeError as e:
        print(f"Error al registrar el evento: {e}")


def force_cleanup_logs(days: int = 3) -> None:
    """
    Función de limpieza forzada que puede ser llamada manualmente.

    Args:
        days: Número de días para considerar un log como antiguo
              (por defecto 3).
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
