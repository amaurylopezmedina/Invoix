import json
import os
from decimal import Decimal

import pyodbc

from db.uDB import ConectarDB


def fetch_invoice_data(cn1, RNCemisor, eNCF):
    try:

        # conn = pyodbc.connect(get_connection_string())
        # cursor = conn.cursor()

        # Fetch selected caja from config
        # config = load_config()
        # selected_caja = config.get('selected_caja', None)
        # if not selected_caja:
        #    raise ValueError("No se ha configurado una caja. Configúrela en ConfigWindow2.")

        # Fetch invoice data
        query = f"Select * from vFEEncabezado where RNCemisor = '{RNCemisor.strip()}' and eNCF = '{eNCF.strip()}'"
        vFEEncabezado = cn1.fetch_query(query)

        query = f"SELECT * FROM vFETotales where eNCF='{eNCF.strip()}' and RNCEmisor = '{RNCemisor.strip()}'"
        qTotales = cn1.fetch_query(query)

        if not vFEEncabezado:
            raise ValueError(
                f"No se encontró factura con RNCemisor {RNCemisor.strip()} y eNCF {eNCF.strip()}"
            )

        company_data = {
            "nombre_empresa": vFEEncabezado[0].RazonSocialEmisor,
            "direccion": vFEEncabezado[0].DireccionEmisor,
            "rnc": vFEEncabezado[0].RNCEmisor,
            "telefono": vFEEncabezado[
                0
            ].TelefonoEmisor1,  # Pendiente arreglar para agregar lso telefonos de EmisorTeleofno
        }

        invoice_data = {
            "cliente": vFEEncabezado[0].CodigoInternoComprador,
            "nombre_cliente": vFEEncabezado[0].RazonSocialComprador,
            "cedula": vFEEncabezado[0].RNCComprador or "",
            "telefono_cliente": vFEEncabezado[0].TelefonoAdicional or "",
            "direccion_cliente": vFEEncabezado[0].DireccionComprador or "",
            "ncf": vFEEncabezado[0].eNCF,
            "tipoecf": vFEEncabezado[0].TipoECF,
            "ncf_type": vFEEncabezado[0].TipoECFL1,
            "moneda_type": vFEEncabezado[0].TipoMoneda,
            "moneda_type2": vFEEncabezado[0].TipoMonedaL,
            "tipo": vFEEncabezado[0].TipoDocumento,
            "FechaLimitePago": vFEEncabezado[0].FechaLimitePago
            or "",  # pendiente agregar cajero
            "fVencimientoNCF": vFEEncabezado[0].FechaVencimientoSecuencia or "",
            "numero": vFEEncabezado[0].NumeroFacturaInterna,
            "fecha": vFEEncabezado[0].FechaEmision,
            "vendedor": vFEEncabezado[0].CodigoVendedor or "",
            "nombre_vendedor": vFEEncabezado[0].NombreVendedor or "",
            "numero_vendedor": vFEEncabezado[0].TelefonoEmisor2 or "",
            "almacen": vFEEncabezado[0].Almacen,
            "observacion": vFEEncabezado[0].Observaciones,
            "usuario": vFEEncabezado[0].Creadopor or "",
            "cajero": vFEEncabezado[0].Cajero or "",  # pendiente agregar cajero
            "codigoseguridad": vFEEncabezado[0].CodigoSeguridad,
            "fechafirma": vFEEncabezado[0].FechaFirma,
            "URLQR": vFEEncabezado[0].URLQR,
            "Tasa": (
                1
                if not vFEEncabezado[0].TipoCambio or vFEEncabezado[0].TipoCambio <= 1
                else vFEEncabezado[0].TipoCambio
            ),
            "Ncf_Modificado": vFEEncabezado[0].NCFModificado or "",
            "MontoNCFModificado": vFEEncabezado[0].MontoNCFModificado,
            "NumeroDocumentoNCFModificado": vFEEncabezado[
                0
            ].NumeroDocumentoNCFModificado
            or "",
            "FechaNCFModificado": vFEEncabezado[0].FechaNCFModificado,
            "AbonoNCFModificado": vFEEncabezado[0].AbonoNCFModificado,
            "DescuentoNCFModificado": vFEEncabezado[0].DescuentoNCFModificado,
            "PendienteNCFModificado": vFEEncabezado[0].PendienteNCFModificado,
            "TipoPagoL": vFEEncabezado[0].TipoPagoL,
            "TerminoPago": vFEEncabezado[0].TerminoPago or "",
            "Razon_modificacion": vFEEncabezado[0].RazonModificacion or "",
            "nota": vFEEncabezado[0].NotaPermanente or "",
            "Sucursal": vFEEncabezado[0].Sucursal or "",
            "Pedido": vFEEncabezado[0].NumeroPedidoInterno or "",
            "tipopago": vFEEncabezado[0].TipoPago or "",
            "EI": vFEEncabezado[0].EstadoImpresion or "",
            "NotaPago": vFEEncabezado[0].NotaPago or "",
            "IndicadorMontoGravado": vFEEncabezado[0].IndicadorMontoGravado or 0,
            "subcentro": vFEEncabezado[0].Informacionadicionalcomprador or "",
            "zona": vFEEncabezado[0].ZonaVenta or "",
            "ruta": vFEEncabezado[0].RutaVenta or "",
            "DireccionEntrega": vFEEncabezado[0].DireccionEntrega or "",
            "ContactoEntrega": vFEEncabezado[0].ContactoEntrega or "",
            "Ciudad": vFEEncabezado[0].NombrePuertoDesembarque or "",
            "NotaAntesProducto": vFEEncabezado[0].NotaAntesDeProductos or "",
            "CorreoElectronico": vFEEncabezado[0].CorreoEmisor or "",
            "ISR_Retenido": vFEEncabezado[0].TotalISRRetencion or Decimal("0.00"),
            "ITBIS_Retenido": vFEEncabezado[0].TotalITBISRetenido or Decimal("0.00"),
            "Monto_total": vFEEncabezado[0].MontoTotal or Decimal("0.00"),
            # Totales
            "Monto_gravado": (
                qTotales[0].MontoGravadoTotal
                if qTotales and hasattr(qTotales[0], "MontoGravadoTotal")
                else vFEEncabezado[0].MontoGravadoTotal
            )
            or Decimal("0.00"),
            "Monto_exento": (
                qTotales[0].MontoExento
                if qTotales and hasattr(qTotales[0], "MontoExento")
                else vFEEncabezado[0].MontoExento
            )
            or Decimal("0.00"),
            "TotalITBIS": (
                qTotales[0].TotalITBIS
                if qTotales and hasattr(qTotales[0], "TotalITBIS")
                else vFEEncabezado[0].TotalITBIS
            )
            or Decimal("0.00"),
            # Monto_pago': qTotales[0].MontoPago or Decimal('0.00')
            # fin de Totales
            # 1 contado 2 credito 3 gratuito
        }

        query = f"Select * from vFETablaDescuentosyRecargos where RNCemisor = '{RNCemisor.strip()}' and eNCF = '{eNCF.strip()}'"
        vFETablaDescuentosyRecargos = cn1.fetch_query(query)

        if vFETablaDescuentosyRecargos and len(vFETablaDescuentosyRecargos) > 0:
            descuento_recargo = {
                "descripcion": vFETablaDescuentosyRecargos[
                    0
                ].DescripcionDescuentooRecargo
                or "",
                "monto": vFETablaDescuentosyRecargos[0].MontoDescuentooRecargo
                or Decimal("0.00"),
            }
        else:
            descuento_recargo = {"descripcion": "", "monto": Decimal("0.00")}
        # Fetch product details
        query = (
            "Select * from vFEDetalle where RNCemisor = '{}' and eNCF = '{}'".format(
                RNCemisor.strip(), eNCF.strip()
            )
        )
        vFEDetalle = cn1.fetch_query(query)

        sql = """
            SELECT 1
            FROM sys.columns
            WHERE Name = 'Lote'
            AND Object_ID = OBJECT_ID('vFEDetalle')
        """

        existe = cn1.fetch_query(sql)

        products = []
        for detail in vFEDetalle:
            # cantidad, product_code, precio, descuen, itbis, monto1 = detail
            Lote = None
            if existe:
                Lote = detail.Lote

            products.append(
                {  # The line ` 'codigo': detail.CodigoItem1,` is creating a key-value pair in a dictionary where the key is 'codigo' and the value is the value of the attribute `CodigoItem1` from the `detail` object. This is part of a loop where for each `detail` in `vFEDetalle`, a dictionary is created with information about a product, and `CodigoItem1` is used to get the product code for that specific detail.
                    "codigo": detail.CodigoItem1 or "",
                    "cantidad": detail.CantidadItem,
                    "descripcion": detail.NombreItem,
                    "precio": detail.PrecioUnitarioItem or Decimal("0.00"),
                    "descuento": detail.DescuentoMonto or Decimal("0.00"),
                    "itbis": detail.MontoITBIS or Decimal("0.00"),
                    "valor": detail.MontoItem,
                    "unidad": detail.UnidadMedidaL or "",
                    "importe": detail.MontoItem,
                    "nota3": detail.NotaImpresion or "",
                    "lote": detail.Lote if existe else "",
                }
            )

        query = f"Select * from vFETablaPago where RNCemisor = '{RNCemisor.strip()}' and eNCF = '{eNCF.strip()}'"
        vFETablaPago = cn1.fetch_query(query)

        forms = []
        for detail2 in vFETablaPago:
            forms.append(
                {
                    "FormaPago": detail2.FormaPago or "",
                    "FormaPagoL": detail2.Descrip or "",
                    "MontoPago": detail2.MontoPago or Decimal("0.00"),
                }
            )

        # --- Consolidación de formas de pago ---
        # Aquí es donde vamos a procesar y consolidar los pagos.

        # Diccionario para almacenar los pagos consolidados (temporalmente)
        pagos_consolidados = {}
        # Lista para almacenar los pagos finales incluyendo la devuelta original si es necesario
        forms_finales = []

        # Primero, consolidamos 'Efectivo' con 'Devuelta'
        for forma in forms:
            forma_pago_l = forma["FormaPagoL"]
            monto_pago = forma["MontoPago"]

            if forma_pago_l == "Efectivo":
                if "Efectivo" in pagos_consolidados:
                    pagos_consolidados["Efectivo"] += monto_pago
                else:
                    pagos_consolidados["Efectivo"] = monto_pago
            elif forma_pago_l == "Devuelta":
                # Sumamos el monto de 'Devuelta' al 'Efectivo' si ya existe,
                # o lo inicializamos con este monto si 'Efectivo' aún no se ha visto.
                if "Efectivo" in pagos_consolidados:
                    pagos_consolidados["Efectivo"] += monto_pago
                else:
                    pagos_consolidados["Efectivo"] = monto_pago
            else:
                # Para otras formas de pago, simplemente sumamos el monto o lo añadimos
                if forma_pago_l in pagos_consolidados:
                    pagos_consolidados[forma_pago_l] += monto_pago
                else:
                    pagos_consolidados[forma_pago_l] = monto_pago

        # Ahora construimos la lista final para `forms_finales`
        # Incluimos el Efectivo consolidado y luego todas las formas de pago originales,
        # incluyendo Devuelta con su monto original si aparece.
        for descripcion, monto in pagos_consolidados.items():
            # Añadimos todas las formas de pago consolidadas excepto la devuelta,
            # ya que la devuelta la añadiremos por separado con su valor original
            if descripcion != "Devuelta":
                forms_finales.append({"FormaPagoL": descripcion, "MontoPago": monto})

        # Agregamos 'Devuelta' con su monto original si estaba presente en los datos iniciales
        for forma_original in forms:
            if forma_original["FormaPagoL"] == "Devuelta":
                forms_finales.append(
                    {
                        "FormaPagoL": forma_original["FormaPagoL"],
                        "MontoPago": forma_original["MontoPago"],
                    }
                )
                break  # Asumimos que solo hay una entrada de 'Devuelta' o solo queremos la primera que aparece

        # Reemplaza la variable original 'forms' con la consolidada y extendida
        forms = forms_finales

        return company_data, invoice_data, products, forms, descuento_recargo
    except (pyodbc.Error, ValueError) as e:
        print("Error:", e)
        return None, None, None
