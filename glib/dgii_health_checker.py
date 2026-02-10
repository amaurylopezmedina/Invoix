"""
Módulo para verificar el estado de los servicios DGII y manejar reintentos inteligentes.
"""

import socket
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Tuple
from urllib.error import URLError

import requests
from requests.exceptions import (
    ConnectionError,
    ConnectTimeout,
    HTTPError,
    ReadTimeout,
    RequestException,
    Timeout,
)
from urllib3.exceptions import NewConnectionError

from config.uGlobalConfig import GConfig
from glib.log_g import log_event, setup_logger

logger = setup_logger("dgii_health_checker.log")


class ServiceStatus(Enum):
    """Estados posibles del servicio DGII"""

    AVAILABLE = "disponible"
    DEGRADED = "degradado"
    UNAVAILABLE = "no_disponible"
    MAINTENANCE = "mantenimiento"
    UNKNOWN = "desconocido"


class ErrorType(Enum):
    """Tipos de errores para decidir si reintentar"""

    NETWORK = "red"  # Reintentar
    TIMEOUT = "timeout"  # Reintentar
    SERVER_ERROR = "servidor"  # Reintentar (5xx)
    CLIENT_ERROR = "cliente"  # NO reintentar (4xx)
    VALIDATION_ERROR = "validacion"  # NO reintentar
    MAINTENANCE = "mantenimiento"  # Reintentar más tarde
    UNKNOWN = "desconocido"  # Reintentar con precaución


class DGIIHealthChecker:
    """
    Verificador de salud de servicios DGII con caché de estado.
    """

    def __init__(self, cache_duration_seconds: int = 60):
        """
        Args:
            cache_duration_seconds: Duración del caché de estado del servicio
        """
        self.cache_duration = timedelta(seconds=cache_duration_seconds)
        self._last_check: Optional[datetime] = None
        self._cached_status: ServiceStatus = ServiceStatus.UNKNOWN
        self._consecutive_failures: int = 0

    def check_service_health(self, force_check: bool = False) -> ServiceStatus:
        """
        Verifica el estado de salud de los servicios DGII.

        Args:
            force_check: Forzar verificación ignorando caché

        Returns:
            ServiceStatus actual del servicio
        """
        # Usar caché si está vigente
        if not force_check and self._is_cache_valid():
            log_event(
                logger,
                "debug",
                f"Usando estado cacheado: {self._cached_status.value}",
            )
            return self._cached_status

        # Verificar servicio
        status = self._perform_health_check()
        self._cached_status = status
        self._last_check = datetime.now()

        return status

    def _is_cache_valid(self) -> bool:
        """Verifica si el caché de estado es válido"""
        if self._last_check is None:
            return False
        return datetime.now() - self._last_check < self.cache_duration

    def _perform_health_check(self) -> ServiceStatus:
        """
        Realiza verificación real del servicio DGII.

        Returns:
            Estado actual del servicio
        """
        try:
            # URL de estado de servicios DGII
            url = GConfig.FEDGII.URLConsultaEstadoServicios

            log_event(logger, "info", f"Verificando estado de servicios DGII: {url}")

            response = requests.get(
                url,
                timeout=10,
                verify=True,
                headers={"User-Agent": "FE-ASESYS-HealthCheck/1.0"},
            )

            # Analizar respuesta
            if response.status_code == 200:
                # Servicios operativos
                self._consecutive_failures = 0
                log_event(logger, "info", "Servicios DGII operativos")
                return ServiceStatus.AVAILABLE

            elif response.status_code == 401:
                # No autorizado - pero servicio responde, asumir disponible
                self._consecutive_failures = 0
                log_event(
                    logger,
                    "info",
                    "Servicios DGII disponibles (requiere autenticación)",
                )
                return ServiceStatus.AVAILABLE

            elif response.status_code == 503:
                # Servicio en mantenimiento
                self._consecutive_failures += 1
                log_event(logger, "warning", "Servicios DGII en mantenimiento")
                return ServiceStatus.MAINTENANCE

            elif 500 <= response.status_code < 600:
                # Error del servidor
                self._consecutive_failures += 1
                log_event(
                    logger,
                    "warning",
                    f"Servicios DGII degradados (HTTP {response.status_code})",
                )
                return ServiceStatus.DEGRADED

            else:
                # Otros códigos
                log_event(
                    logger,
                    "warning",
                    f"Respuesta inesperada de DGII: {response.status_code}",
                )
                return ServiceStatus.UNKNOWN

        except (ConnectionError, ConnectTimeout, ReadTimeout, Timeout) as e:
            self._consecutive_failures += 1
            log_event(
                logger,
                "error",
                f"Error de conectividad con DGII (intento {self._consecutive_failures}): {e}",
            )
            return ServiceStatus.UNAVAILABLE

        except Exception as e:
            self._consecutive_failures += 1
            log_event(logger, "error", f"Error verificando servicios DGII: {e}")
            return ServiceStatus.UNKNOWN

    def should_retry(
        self, error_type: ErrorType, attempt: int, max_attempts: int = 3
    ) -> Tuple[bool, int]:
        """
        Determina si se debe reintentar una operación.

        Args:
            error_type: Tipo de error ocurrido
            attempt: Número de intento actual (1-indexed)
            max_attempts: Máximo de intentos permitidos

        Returns:
            (should_retry, wait_seconds): Si reintentar y cuánto esperar
        """
        # No reintentar errores de validación o cliente
        if error_type in [ErrorType.VALIDATION_ERROR, ErrorType.CLIENT_ERROR]:
            log_event(
                logger,
                "info",
                f"No se reintenta error tipo {error_type.value}",
            )
            return False, 0

        # Verificar límite de intentos
        if attempt >= max_attempts:
            log_event(
                logger,
                "warning",
                f"Máximo de intentos alcanzado ({max_attempts})",
            )
            return False, 0

        # Calcular backoff exponencial
        wait_seconds = self._calculate_backoff(error_type, attempt)

        # Verificar estado del servicio antes de reintentar
        service_status = self.check_service_health()

        if service_status == ServiceStatus.UNAVAILABLE:
            # Servicio no disponible, esperar más tiempo
            wait_seconds *= 2
            log_event(
                logger,
                "warning",
                f"Servicio DGII no disponible. Esperando {wait_seconds}s antes de reintentar",
            )

        elif service_status == ServiceStatus.MAINTENANCE:
            # Mantenimiento, esperar 5 minutos
            wait_seconds = 300
            log_event(
                logger,
                "warning",
                f"Servicio DGII en mantenimiento. Esperando {wait_seconds}s",
            )

        return True, wait_seconds

    def _calculate_backoff(self, error_type: ErrorType, attempt: int) -> int:
        """
        Calcula tiempo de espera con backoff exponencial.

        Args:
            error_type: Tipo de error
            attempt: Número de intento

        Returns:
            Segundos a esperar
        """
        # Backoff base según tipo de error
        base_backoff = {
            ErrorType.NETWORK: 5,
            ErrorType.TIMEOUT: 10,
            ErrorType.SERVER_ERROR: 15,
            ErrorType.MAINTENANCE: 60,
            ErrorType.UNKNOWN: 10,
        }

        base = base_backoff.get(error_type, 10)

        # Backoff exponencial: base * 2^(attempt-1)
        # Intento 1: base, Intento 2: base*2, Intento 3: base*4
        backoff = base * (2 ** (attempt - 1))

        # Máximo 300 segundos (5 minutos)
        return min(backoff, 300)

    def classify_error(self, exception: Exception) -> ErrorType:
        """
        Clasifica un error para determinar estrategia de reintento.

        Args:
            exception: Excepción ocurrida

        Returns:
            Tipo de error clasificado
        """
        error_str = str(exception).lower()

        # 1. Errores de CONEXIÓN (recuperables)
        # ConnectionError: DNS failure, connection refused, network unreachable
        if isinstance(exception, (ConnectionError, ConnectTimeout)):
            log_event(
                logger,
                "warning",
                f"🔌 Error de conexión detectado: {type(exception).__name__} - {exception}",
            )
            return ErrorType.NETWORK

        # NewConnectionError (urllib3) - No se pudo crear nueva conexión
        if NewConnectionError and isinstance(exception, NewConnectionError):
            log_event(logger, "warning", f"🔌 Sin internet/nueva conexión: {exception}")
            return ErrorType.NETWORK

        # MaxRetryError (urllib3) - Máximo de reintentos alcanzado
        if MaxRetryError and isinstance(exception, MaxRetryError):
            log_event(
                logger,
                "warning",
                f"🔌 Sin respuesta después de múltiples intentos: {exception}",
            )
            return ErrorType.NETWORK

        # SSLError - Problemas con certificados SSL/TLS
        if SSLError and isinstance(exception, SSLError):
            log_event(logger, "warning", f"🔒 Error de certificado SSL: {exception}")
            return ErrorType.NETWORK

        # ProxyError - Problemas con proxy
        if ProxyError and isinstance(exception, ProxyError):
            log_event(logger, "warning", f"🔌 Error de proxy: {exception}")
            return ErrorType.NETWORK

        # Socket errors (DNS resolution, network errors)
        if isinstance(exception, (socket.gaierror, socket.timeout, OSError)):
            log_event(
                logger,
                "warning",
                f"🌐 Error de socket/red detectado: {type(exception).__name__} - {exception}",
            )
            return ErrorType.NETWORK

        # URLError (de urllib)
        if isinstance(exception, URLError):
            log_event(logger, "warning", f"🔗 Error de URL detectado: {exception}")
            return ErrorType.NETWORK

        # RequestException genérica (base class)
        # Captura cualquier error de requests no específico
        if isinstance(exception, RequestException):
            # Verificar si es realmente de conexión o sin internet
            connection_keywords = [
                "connection",
                "refused",
                "unreachable",
                "dns",
                "resolve",
                "network",
                "timed out",
                "failed to establish",
                "no internet",
                "offline",
                "no route",
                "host unreachable",
                "network is down",
                "adapter",
                "cannot assign",
                "nodename nor servname",
            ]

            if any(keyword in error_str for keyword in connection_keywords):
                log_event(
                    logger,
                    "warning",
                    f"🔌 Error de conexión/sin internet (RequestException): {exception}",
                )
                return ErrorType.NETWORK

        # 2. Errores de TIMEOUT (recuperables)
        if isinstance(exception, (ReadTimeout, Timeout)):
            log_event(
                logger,
                "warning",
                f"⏱️ Timeout detectado: {type(exception).__name__} - {exception}",
            )
            return ErrorType.TIMEOUT

        # 3. Errores HTTP específicos
        if isinstance(exception, HTTPError):
            if hasattr(exception, "response"):
                status_code = exception.response.status_code
                if status_code == 503:
                    log_event(
                        logger, "warning", f"⏸️ Mantenimiento DGII detectado (HTTP 503)"
                    )
                    return ErrorType.MAINTENANCE
                elif 500 <= status_code < 600:
                    log_event(
                        logger,
                        "warning",
                        f"⚠️ Error del servidor DGII (HTTP {status_code})",
                    )
                    return ErrorType.SERVER_ERROR
                elif 400 <= status_code < 500:
                    log_event(
                        logger, "info", f"❌ Error del cliente (HTTP {status_code})"
                    )
                    return ErrorType.CLIENT_ERROR

        # 4. Errores de validación (NO recuperables)
        if "validacion" in error_str or "schema" in error_str or "invalid" in error_str:
            log_event(logger, "error", f"📋 Error de validación detectado: {exception}")
            return ErrorType.VALIDATION_ERROR

        # 5. Error desconocido
        log_event(
            logger,
            "warning",
            f"❓ Error no clasificado: {type(exception).__name__} - {exception}",
        )
        return ErrorType.UNKNOWN

    def get_retry_message(
        self, error_type: ErrorType, attempt: int, wait_seconds: int
    ) -> str:
        """
        Genera mensaje descriptivo para logging de reintentos.

        Args:
            error_type: Tipo de error
            attempt: Número de intento
            wait_seconds: Segundos a esperar

        Returns:
            Mensaje formateado
        """
        messages = {
            ErrorType.NETWORK: f"Error de red. Reintento {attempt} en {wait_seconds}s",
            ErrorType.TIMEOUT: f"Timeout. Reintento {attempt} en {wait_seconds}s",
            ErrorType.SERVER_ERROR: f"Error del servidor DGII. Reintento {attempt} en {wait_seconds}s",
            ErrorType.MAINTENANCE: f"Mantenimiento DGII. Reintento {attempt} en {wait_seconds}s",
            ErrorType.UNKNOWN: f"Error desconocido. Reintento {attempt} en {wait_seconds}s",
        }

        return messages.get(error_type, f"Reintento {attempt} en {wait_seconds}s")


# Instancia global para reutilización
_health_checker: Optional[DGIIHealthChecker] = None


def get_health_checker() -> DGIIHealthChecker:
    """
    Obtiene la instancia singleton del health checker.

    Returns:
        Instancia de DGIIHealthChecker
    """
    global _health_checker
    if _health_checker is None:
        _health_checker = DGIIHealthChecker(cache_duration_seconds=60)
    return _health_checker


def execute_with_retry(
    operation_func,
    operation_name: str,
    max_attempts: int = 3,
    *args,
    **kwargs,
):
    """
    Ejecuta una operación con lógica de reintento inteligente.

    Args:
        operation_func: Función a ejecutar
        operation_name: Nombre de la operación (para logging)
        max_attempts: Máximo de intentos
        *args, **kwargs: Argumentos para la función

    Returns:
        Resultado de la operación

    Raises:
        Exception: Si falla después de todos los reintentos
    """
    health_checker = get_health_checker()
    last_exception = None

    for attempt in range(1, max_attempts + 1):
        try:
            log_event(
                logger,
                "info",
                f"Ejecutando {operation_name} (intento {attempt}/{max_attempts})",
            )

            # Verificar estado del servicio antes de intentar
            if attempt > 1:
                service_status = health_checker.check_service_health()
                if service_status == ServiceStatus.UNAVAILABLE:
                    log_event(
                        logger,
                        "warning",
                        f"Servicio no disponible, posponiendo {operation_name}",
                    )
                    raise ConnectionError("Servicio DGII no disponible")

            # Ejecutar operación
            result = operation_func(*args, **kwargs)

            # Éxito
            log_event(
                logger,
                "info",
                f"{operation_name} completado exitosamente en intento {attempt}",
            )
            return result

        except Exception as e:
            last_exception = e
            error_type = health_checker.classify_error(e)

            log_event(
                logger,
                "error",
                f"Error en {operation_name} (intento {attempt}): {e}",
            )

            # Decidir si reintentar
            should_retry, wait_seconds = health_checker.should_retry(
                error_type, attempt, max_attempts
            )

            if not should_retry:
                log_event(
                    logger,
                    "error",
                    f"{operation_name} falló sin posibilidad de reintento: {error_type.value}",
                )
                raise

            # Esperar antes de reintentar
            retry_msg = health_checker.get_retry_message(
                error_type, attempt, wait_seconds
            )
            log_event(logger, "warning", retry_msg)
            time.sleep(wait_seconds)

    # Si llegamos aquí, fallaron todos los intentos
    log_event(
        logger,
        "error",
        f"{operation_name} falló después de {max_attempts} intentos",
    )
    raise last_exception
