"""
Tests unitarios para el sistema de Health Checking de DGII.

Para ejecutar:
    pytest tests/test_dgii_health_checker.py -v
"""

import time
from unittest.mock import Mock, patch

import pytest
from requests.exceptions import ConnectionError, ReadTimeout, Timeout

from glib.dgii_health_checker import (
    DGIIHealthChecker,
    ErrorType,
    ServiceStatus,
    execute_with_retry,
    get_health_checker,
)


class TestDGIIHealthChecker:
    """Tests para la clase DGIIHealthChecker"""

    def test_classify_error_network(self):
        """Debe clasificar ConnectionError como NETWORK"""
        health_checker = DGIIHealthChecker()
        error = ConnectionError("Connection refused")

        error_type = health_checker.classify_error(error)

        assert error_type == ErrorType.NETWORK

    def test_classify_error_timeout(self):
        """Debe clasificar Timeout como TIMEOUT"""
        health_checker = DGIIHealthChecker()
        error = ReadTimeout("Read timeout")

        error_type = health_checker.classify_error(error)

        assert error_type == ErrorType.TIMEOUT

    def test_classify_error_validation(self):
        """Debe clasificar errores de validación"""
        health_checker = DGIIHealthChecker()
        error = Exception("Validacion de schema falló")

        error_type = health_checker.classify_error(error)

        assert error_type == ErrorType.VALIDATION_ERROR

    def test_should_retry_validation_error(self):
        """No debe reintentar errores de validación"""
        health_checker = DGIIHealthChecker()

        should_retry, wait_seconds = health_checker.should_retry(
            ErrorType.VALIDATION_ERROR, attempt=1, max_attempts=3
        )

        assert should_retry is False
        assert wait_seconds == 0

    def test_should_retry_network_error(self):
        """Debe reintentar errores de red"""
        health_checker = DGIIHealthChecker()

        with patch.object(
            health_checker, "check_service_health", return_value=ServiceStatus.AVAILABLE
        ):
            should_retry, wait_seconds = health_checker.should_retry(
                ErrorType.NETWORK, attempt=1, max_attempts=3
            )

        assert should_retry is True
        assert wait_seconds > 0

    def test_should_retry_max_attempts_reached(self):
        """No debe reintentar cuando se alcanza el máximo"""
        health_checker = DGIIHealthChecker()

        should_retry, wait_seconds = health_checker.should_retry(
            ErrorType.NETWORK, attempt=3, max_attempts=3
        )

        assert should_retry is False

    def test_calculate_backoff_exponential(self):
        """Debe calcular backoff exponencial correctamente"""
        health_checker = DGIIHealthChecker()

        # Intento 1: base * 2^0 = 5
        backoff1 = health_checker._calculate_backoff(ErrorType.NETWORK, 1)
        assert backoff1 == 5

        # Intento 2: base * 2^1 = 10
        backoff2 = health_checker._calculate_backoff(ErrorType.NETWORK, 2)
        assert backoff2 == 10

        # Intento 3: base * 2^2 = 20
        backoff3 = health_checker._calculate_backoff(ErrorType.NETWORK, 3)
        assert backoff3 == 20

    def test_calculate_backoff_max_limit(self):
        """Debe limitar el backoff a 300 segundos"""
        health_checker = DGIIHealthChecker()

        # Con muchos intentos debería llegar al máximo
        backoff = health_checker._calculate_backoff(ErrorType.MAINTENANCE, 10)

        assert backoff <= 300

    def test_cache_validity(self):
        """Debe usar caché cuando es válido"""
        health_checker = DGIIHealthChecker(cache_duration_seconds=10)

        with patch.object(
            health_checker,
            "_perform_health_check",
            return_value=ServiceStatus.AVAILABLE,
        ) as mock_check:
            # Primera llamada - debe consultar
            status1 = health_checker.check_service_health()
            assert mock_check.call_count == 1

            # Segunda llamada - debe usar caché
            status2 = health_checker.check_service_health()
            assert mock_check.call_count == 1

            assert status1 == status2 == ServiceStatus.AVAILABLE

    def test_cache_forced_check(self):
        """Debe ignorar caché con force_check=True"""
        health_checker = DGIIHealthChecker(cache_duration_seconds=10)

        with patch.object(
            health_checker,
            "_perform_health_check",
            return_value=ServiceStatus.AVAILABLE,
        ) as mock_check:
            # Primera llamada
            health_checker.check_service_health()
            assert mock_check.call_count == 1

            # Segunda llamada forzada - debe consultar de nuevo
            health_checker.check_service_health(force_check=True)
            assert mock_check.call_count == 2

    @patch("glib.dgii_health_checker.requests.get")
    def test_perform_health_check_success(self, mock_get):
        """Debe detectar servicio disponible correctamente"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        health_checker = DGIIHealthChecker()
        status = health_checker._perform_health_check()

        assert status == ServiceStatus.AVAILABLE
        assert health_checker._consecutive_failures == 0

    @patch("glib.dgii_health_checker.requests.get")
    def test_perform_health_check_maintenance(self, mock_get):
        """Debe detectar mantenimiento correctamente"""
        mock_response = Mock()
        mock_response.status_code = 503
        mock_get.return_value = mock_response

        health_checker = DGIIHealthChecker()
        status = health_checker._perform_health_check()

        assert status == ServiceStatus.MAINTENANCE

    @patch("glib.dgii_health_checker.requests.get")
    def test_perform_health_check_timeout(self, mock_get):
        """Debe detectar timeout como no disponible"""
        mock_get.side_effect = Timeout("Connection timeout")

        health_checker = DGIIHealthChecker()
        status = health_checker._perform_health_check()

        assert status == ServiceStatus.UNAVAILABLE

    def test_get_retry_message(self):
        """Debe generar mensajes descriptivos"""
        health_checker = DGIIHealthChecker()

        msg = health_checker.get_retry_message(
            ErrorType.NETWORK, attempt=2, wait_seconds=10
        )

        assert "red" in msg.lower()
        assert "2" in msg
        assert "10" in msg


class TestExecuteWithRetry:
    """Tests para la función execute_with_retry"""

    def test_execute_with_retry_success_first_attempt(self):
        """Debe retornar resultado en primer intento exitoso"""
        mock_func = Mock(return_value="success")

        result = execute_with_retry(mock_func, "test_operation", max_attempts=3)

        assert result == "success"
        assert mock_func.call_count == 1

    def test_execute_with_retry_success_after_retries(self):
        """Debe retornar resultado después de reintentos"""
        mock_func = Mock(
            side_effect=[
                ConnectionError("Network error"),
                ConnectionError("Network error"),
                "success",
            ]
        )

        with patch("glib.dgii_health_checker.time.sleep"):
            result = execute_with_retry(mock_func, "test_operation", max_attempts=3)

        assert result == "success"
        assert mock_func.call_count == 3

    def test_execute_with_retry_validation_error_no_retry(self):
        """No debe reintentar errores de validación"""
        mock_func = Mock(side_effect=Exception("Validacion falló"))

        with pytest.raises(Exception, match="Validacion"):
            execute_with_retry(mock_func, "test_operation", max_attempts=3)

        # Solo debe intentar una vez
        assert mock_func.call_count == 1

    def test_execute_with_retry_max_attempts_exceeded(self):
        """Debe fallar después del máximo de intentos"""
        mock_func = Mock(side_effect=ConnectionError("Network error"))

        with patch("glib.dgii_health_checker.time.sleep"):
            with pytest.raises(ConnectionError):
                execute_with_retry(mock_func, "test_operation", max_attempts=3)

        assert mock_func.call_count == 3


class TestHelperFunctions:
    """Tests para funciones auxiliares"""

    def test_get_health_checker_singleton(self):
        """Debe retornar la misma instancia (singleton)"""
        checker1 = get_health_checker()
        checker2 = get_health_checker()

        assert checker1 is checker2


# Tests de integración
class TestIntegration:
    """Tests de integración del sistema completo"""

    @patch("glib.dgii_health_checker.requests.get")
    def test_integration_service_down_then_up(self, mock_get):
        """
        Simula servicio caído que luego se recupera
        """
        # Primera llamada: servicio caído
        mock_get.side_effect = [
            Timeout("Connection timeout"),
            # Segunda verificación: servicio disponible
            Mock(status_code=200),
        ]

        health_checker = DGIIHealthChecker(cache_duration_seconds=1)

        # Verificar estado caído
        status1 = health_checker.check_service_health(force_check=True)
        assert status1 == ServiceStatus.UNAVAILABLE

        # Esperar para invalidar caché
        time.sleep(1.1)

        # Verificar recuperación
        status2 = health_checker.check_service_health(force_check=True)
        assert status2 == ServiceStatus.AVAILABLE

    def test_integration_retry_logic_with_backoff(self):
        """
        Verifica que el sistema implemente backoff correctamente
        """
        attempt_times = []

        def failing_operation():
            attempt_times.append(time.time())
            if len(attempt_times) < 3:
                raise ConnectionError("Network error")
            return "success"

        with patch("glib.dgii_health_checker.time.sleep") as mock_sleep:
            result = execute_with_retry(
                failing_operation, "test_operation", max_attempts=3
            )

        assert result == "success"
        assert len(attempt_times) == 3
        # Debe haber llamado a sleep 2 veces (entre los 3 intentos)
        assert mock_sleep.call_count == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
