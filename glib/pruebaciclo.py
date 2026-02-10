import time

# ============================================================================
# VARIABLES FIJAS
# ============================================================================
RNCEmisor = "101234567"
eNCF = "E310000000001"


# Encabezado (ERP)
class Encabezado:
    def __init__(self, monto):
        self.MontoTotal = monto


qEncabezadoFactura = [Encabezado(1000.00)]  # <-- encabezado ERP


# ============================================================================
# LOGGER
# ============================================================================
def log_event(logger, level, msg):
    print(f"[{level.upper()}] {msg}")


logger = None


# ============================================================================
# MOCK CN1
# ============================================================================
class CNMock:

    def __init__(self):
        self.intentos = 0
        self.detalle = []

    def _get_detalle(self, rnc, encf):
        self.intentos += 1

        # Detalle SOLO aparece en el segundo intento
        if self.intentos < 2:
            return []

        self.detalle = [
            {"item": 1, "MontoTotal": 400.00},
            {"item": 2, "MontoTotal": 500.00},
        ]
        return self.detalle

    def _count_detalle(self, rnc, encf):
        return len(self.detalle)

    def vista_existe(self, vista):
        return True

    def _get_totales(self, rnc, encf):
        # Totales = SUMA REAL del detalle
        class Totales:
            def __init__(self, monto):
                self.MontoTotal = monto

        total_detalle = sum(d["MontoTotal"] for d in self.detalle)
        return [Totales(total_detalle)]


cn1 = CNMock()

# ============================================================================
# VALIDACIÓN CRÍTICA
# ============================================================================
qTotales = None

for intento in range(1, 3):

    log_event(logger, "info", f"Iniciando intento {intento} para buscar el detalle")

    qDetalleFactura = cn1._get_detalle(RNCEmisor.strip(), eNCF.strip())

    # ------------------------------------------------------------------------
    # CASO A) NO EXISTE DETALLE
    # ------------------------------------------------------------------------
    if not qDetalleFactura:
        if intento == 2:
            msg = "No hay datos de detalle para el Encabezado."
            log_event(logger, "error", msg)
            print("RETORNO:", "62", msg)
            break
        else:
            log_event(logger, "info", "Sin detalle, reintentando...")
            time.sleep(0.4)
            continue

    # ------------------------------------------------------------------------
    # CASO B) EXISTE DETALLE → VALIDAR TOTALES
    # ------------------------------------------------------------------------
    if cn1.vista_existe("vFETotales"):
        qTotales = cn1._get_totales(RNCEmisor.strip(), eNCF.strip())

        if qTotales:
            diferencia = abs(qEncabezadoFactura[0].MontoTotal - qTotales[0].MontoTotal)

            print(
                f"DEBUG → Encabezado: {qEncabezadoFactura[0].MontoTotal} | "
                f"Detalle: {qTotales[0].MontoTotal} | "
                f"Diferencia: {diferencia}"
            )

            if round(diferencia, 2) > 1:

                if intento < 2:
                    log_event(
                        logger,
                        "error",
                        "Los montos totales no coinciden, reintentando...",
                    )
                    time.sleep(0.4)
                    continue

                msg = "Los Montos Totales del Detalle y del Encabezado no coinciden."
                log_event(logger, "error", msg)
                print("RETORNO:", "61", msg)
                break

    # ------------------------------------------------------------------------
    # CASO C) OK
    # ------------------------------------------------------------------------
    log_event(
        logger,
        "info",
        f"Detalle encontrado: {cn1._count_detalle(RNCEmisor.strip(), eNCF.strip())}",
    )
    print("✔ VALIDACIÓN COMPLETA")
    break
