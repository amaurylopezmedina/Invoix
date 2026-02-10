
   WITH
  e AS (
    SELECT 
      rnc,
	  ambiente
    FROM
      empresa
    WITH (NOLOCK)
  ),
 AmbienteInfo AS (
    SELECT TOP 1 
        A.AMBIENTE, 
        A.DESCRIP, 
        ISNULL(A.RUTA, '') AS RUTA 
    FROM FEAmbiente A WITH (NOLOCK)
	cross join e
    WHERE A.RUTA IS NOT NULL and a.ambiente = e.ambiente
    ORDER BY A.AMBIENTE  -- Aseguramos un orden consistente
)
SELECT        TipoECF, eNCF, FechaVencimientoSecuencia, IndicadorNotaCredito, IndicadorEnvioDiferido, IndicadorMontoGravado, TipoIngresos, TipoPago, FechaLimitePago, TerminoPago, FormaPago1, MontoPago1, FormaPago2, 
                         MontoPago2, FormaPago3, MontoPago3, FormaPago4, MontoPago4, FormaPago5, MontoPago5, FormaPago6, MontoPago6, FormaPago7, MontoPago7, TipoCuentaPago, NumeroCuentaPago, BancoPago, FechaDesde, 
                         FechaHasta, TotalPaginas, RNCEmisor, RazonSocialEmisor, NombreComercial, Sucursal, DireccionEmisor, Municipio, Provincia, TelefonoEmisor1, TelefonoEmisor2, TelefonoEmisor3, CorreoEmisor, WebSite, 
                         ActividadEconomica, CodigoVendedor, NumeroFacturaInterna, NumeroPedidoInterno, ZonaVenta, RutaVenta, InformacionAdicionalEmisor, FechaEmision, RNCComprador, IdentificadorExtranjero, RazonSocialComprador, 
                         ContactoComprador, CorreoComprador, DireccionComprador, MunicipioComprador, ProvinciaComprador, PaisComprador, FechaEntrega, ContactoEntrega, DireccionEntrega, TelefonoAdicional, FechaOrdenCompra, 
                         NumeroOrdenCompra, CodigoInternoComprador, ResponsablePago, Informacionadicionalcomprador, FechaEmbarque, NumeroEmbarque, NumeroContenedor, NumeroReferencia, NombrePuertoEmbarque, CondicionesEntrega, 
                         TotalFob, Seguro, Flete, OtrosGastos, TotalCif, RegimenAduanero, NombrePuertoSalida, NombrePuertoDesembarque, PesoBruto, PesoNeto, UnidadPesoBruto, UnidadPesoNeto, CantidadBulto, UnidadBulto, VolumenBulto, 
                         UnidadVolumen, ViaTransporte, PaisOrigen, DireccionDestino, PaisDestino, RNCIdentificacionCompaniaTransportista, NombreCompaniaTransportista, NumeroViaje, Conductor, DocumentoTransporte, Ficha, Placa, 
                         RutaTransporte, ZonaTransporte, NumeroAlbaran, MontoGravadoTotal, MontoGravadoI1, MontoGravadoI2, MontoGravadoI3, MontoExento, ITBIS1, ITBIS2, ITBIS3, TotalITBIS, TotalITBIS1, TotalITBIS2, TotalITBIS3, 
                         MontoImpuestoAdicional, TipoImpuesto1, TasaImpuestoAdicional1, MontoImpuestoSelectivoConsumoEspecifico1, MontoImpuestoSelectivoConsumoAdvalorem1, OtrosImpuestosAdicionales1, TipoImpuesto2, 
                         TasaImpuestoAdicional2, MontoImpuestoSelectivoConsumoEspecifico2, MontoImpuestoSelectivoConsumoAdvalorem2, OtrosImpuestosAdicionales2, TipoImpuesto3, TasaImpuestoAdicional3, 
                         MontoImpuestoSelectivoConsumoEspecifico3, MontoImpuestoSelectivoConsumoAdvalorem3, OtrosImpuestosAdicionales3, TipoImpuesto4, TasaImpuestoAdicional4, MontoImpuestoSelectivoConsumoEspecifico4, 
                         MontoImpuestoSelectivoConsumoAdvalorem4, OtrosImpuestosAdicionales4, MontoTotal, MontoNoFacturable, MontoPeriodo, SaldoAnterior, MontoAvancePago, ValorPagar, TotalITBISRetenido, TotalISRRetencion, 
                         TotalITBISPercepcion, TotalISRPercepcion, TipoMoneda, TipoCambio, MontoGravadoTotalOtraMoneda, MontoGravado1OtraMoneda, MontoGravado2OtraMoneda, MontoGravado3OtraMoneda, MontoExentoOtraMoneda, 
                         TotalITBISOtraMoneda, TotalITBIS1OtraMoneda, TotalITBIS2OtraMoneda, TotalITBIS3OtraMoneda, MontoImpuestoAdicionalOtraMoneda, TipoImpuestoOtraMoneda1, TasaImpuestoAdicionalOtraMoneda1, 
                         MontoImpuestoSelectivoConsumoEspecificoOtraMoneda1, MontoImpuestoSelectivoConsumoAdvaloremOtraMoneda1, OtrosImpuestosAdicionalesOtraMoneda1, TipoImpuestoOtraMoneda2, TasaImpuestoAdicionalOtraMoneda2, 
                         MontoImpuestoSelectivoConsumoEspecificoOtraMoneda2, MontoImpuestoSelectivoConsumoAdvaloremOtraMoneda2, OtrosImpuestosAdicionalesOtraMoneda2, TipoImpuestoOtraMoneda3, TasaImpuestoAdicionalOtraMoneda3, 
                         MontoImpuestoSelectivoConsumoEspecificoOtraMoneda3, MontoImpuestoSelectivoConsumoAdvaloremOtraMoneda3, OtrosImpuestosAdicionalesOtraMoneda3, TipoImpuestoOtraMoneda4, TasaImpuestoAdicionalOtraMoneda4, 
                         MontoImpuestoSelectivoConsumoEspecificoOtraMoneda4, MontoImpuestoSelectivoConsumoAdvaloremOtraMoneda4, OtrosImpuestosAdicionalesOtraMoneda4, MontoTotalOtraMoneda, trackid, FechaFirma, CodigoSeguridad, 
                         CodigoSeguridadCF, EstadoFiscal,  fechacreacion, EstadoImpresion, ConteoImpresiones, transferencia, Modificado, ResultadoEstadoFiscal, MontoDGII, MontoITBISDGII, TipoImpuesto5, TasaImpuestoAdicional5, 
                         MontoImpuestoSelectivoConsumoEspecifico5, MontoImpuestoSelectivoConsumoAdvalorem5, OtrosImpuestosAdicionales5, TipoImpuesto6, TasaImpuestoAdicional6, MontoImpuestoSelectivoConsumoEspecifico6, 
                         MontoImpuestoSelectivoConsumoAdvalorem6, OtrosImpuestosAdicionales6, TipoImpuesto7, TasaImpuestoAdicional7, MontoImpuestoSelectivoConsumoEspecifico7, MontoImpuestoSelectivoConsumoAdvalorem7, 
                         OtrosImpuestosAdicionales7, TipoImpuesto8, TasaImpuestoAdicional8, MontoImpuestoSelectivoConsumoEspecifico8, MontoImpuestoSelectivoConsumoAdvalorem8, OtrosImpuestosAdicionales8, TipoImpuesto9, 
                         TasaImpuestoAdicional9, MontoImpuestoSelectivoConsumoEspecifico9, MontoImpuestoSelectivoConsumoAdvalorem9, OtrosImpuestosAdicionales9, TipoImpuesto10, TasaImpuestoAdicional10, 
                         MontoImpuestoSelectivoConsumoEspecifico10, MontoImpuestoSelectivoConsumoAdvalorem10, OtrosImpuestosAdicionales10, TipoImpuesto11, TasaImpuestoAdicional11, MontoImpuestoSelectivoConsumoEspecifico11, 
                         MontoImpuestoSelectivoConsumoAdvalorem11, OtrosImpuestosAdicionales11, TipoImpuesto12, TasaImpuestoAdicional12, MontoImpuestoSelectivoConsumoEspecifico12, MontoImpuestoSelectivoConsumoAdvalorem12, 
                         OtrosImpuestosAdicionales12, TipoImpuesto13, TasaImpuestoAdicional13, MontoImpuestoSelectivoConsumoEspecifico13, MontoImpuestoSelectivoConsumoAdvalorem13, OtrosImpuestosAdicionales13, TipoImpuesto14, 
                         TasaImpuestoAdicional14, MontoImpuestoSelectivoConsumoEspecifico14, MontoImpuestoSelectivoConsumoAdvalorem14, OtrosImpuestosAdicionales14, TipoImpuesto15, TasaImpuestoAdicional15, 
                         MontoImpuestoSelectivoConsumoEspecifico15, MontoImpuestoSelectivoConsumoAdvalorem15, OtrosImpuestosAdicionales15, TipoImpuesto16, TasaImpuestoAdicional16, MontoImpuestoSelectivoConsumoEspecifico16, 
                         MontoImpuestoSelectivoConsumoAdvalorem16, OtrosImpuestosAdicionales16, TipoImpuesto17, TasaImpuestoAdicional17, MontoImpuestoSelectivoConsumoEspecifico17, MontoImpuestoSelectivoConsumoAdvalorem17, 
                         OtrosImpuestosAdicionales17, TipoImpuesto18, TasaImpuestoAdicional18, MontoImpuestoSelectivoConsumoEspecifico18, MontoImpuestoSelectivoConsumoAdvalorem18, OtrosImpuestosAdicionales18, TipoImpuesto19, 
                         TasaImpuestoAdicional19, MontoImpuestoSelectivoConsumoEspecifico19, MontoImpuestoSelectivoConsumoAdvalorem19, OtrosImpuestosAdicionales19, TipoImpuesto20, TasaImpuestoAdicional20, 
                         MontoImpuestoSelectivoConsumoEspecifico20, MontoImpuestoSelectivoConsumoAdvalorem20, OtrosImpuestosAdicionales20, NumeroLineaDoR1, TipoAjuste1, IndicadorNorma10071, DescripcionDescuentooRecargo1, 
                         TipoValor1, ValorDescuentooRecargo1, MontoDescuentooRecargo1, MontoDescuentooRecargoOtraMoneda1, IndicadorFacturacionDescuentooRecargo1, NumeroLineaDoR2, TipoAjuste2, IndicadorNorma10072, 
                         DescripcionDescuentooRecargo2, TipoValor2, ValorDescuentooRecargo2, MontoDescuentooRecargo2, MontoDescuentooRecargoOtraMoneda2, IndicadorFacturacionDescuentooRecargo2, NumeroLineaDoR3, TipoAjuste3, 
                         IndicadorNorma10073, DescripcionDescuentooRecargo3, TipoValor3, ValorDescuentooRecargo3, MontoDescuentooRecargo3, MontoDescuentooRecargoOtraMoneda3, IndicadorFacturacionDescuentooRecargo3, 
                         NumeroLineaDoR4, TipoAjuste4, IndicadorNorma10074, DescripcionDescuentooRecargo4, TipoValor4, ValorDescuentooRecargo4, MontoDescuentooRecargo4, MontoDescuentooRecargoOtraMoneda4, 
                         IndicadorFacturacionDescuentooRecargo4, NumeroLineaDoR5, TipoAjuste5, IndicadorNorma10075, DescripcionDescuentooRecargo5, TipoValor5, ValorDescuentooRecargo5, MontoDescuentooRecargo5, 
                         MontoDescuentooRecargoOtraMoneda5, IndicadorFacturacionDescuentooRecargo5, NumeroLineaDoR6, TipoAjuste6, IndicadorNorma10076, DescripcionDescuentooRecargo6, TipoValor6, ValorDescuentooRecargo6, 
                         MontoDescuentooRecargo6, MontoDescuentooRecargoOtraMoneda6, IndicadorFacturacionDescuentooRecargo6, NumeroLineaDoR7, TipoAjuste7, IndicadorNorma10077, DescripcionDescuentooRecargo7, TipoValor7, 
                         ValorDescuentooRecargo7, MontoDescuentooRecargo7, MontoDescuentooRecargoOtraMoneda7, IndicadorFacturacionDescuentooRecargo7, NumeroLineaDoR8, TipoAjuste8, IndicadorNorma10078, 
                         DescripcionDescuentooRecargo8, TipoValor8, ValorDescuentooRecargo8, MontoDescuentooRecargo8, MontoDescuentooRecargoOtraMoneda8, IndicadorFacturacionDescuentooRecargo8, NumeroLineaDoR9, TipoAjuste9, 
                         IndicadorNorma10079, DescripcionDescuentooRecargo9, TipoValor9, ValorDescuentooRecargo9, MontoDescuentooRecargo9, MontoDescuentooRecargoOtraMoneda9, IndicadorFacturacionDescuentooRecargo9, 
                         NumeroLineaDoR10, TipoAjuste10, IndicadorNorma100710, DescripcionDescuentooRecargo10, TipoValor10, ValorDescuentooRecargo10, MontoDescuentooRecargo10, MontoDescuentooRecargoOtraMoneda10, 
                         IndicadorFacturacionDescuentooRecargo10, NumeroLineaDoR11, TipoAjuste11, IndicadorNorma100711, DescripcionDescuentooRecargo11, TipoValor11, ValorDescuentooRecargo11, MontoDescuentooRecargo11, 
                         MontoDescuentooRecargoOtraMoneda11, IndicadorFacturacionDescuentooRecargo11, NumeroLineaDoR12, TipoAjuste12, IndicadorNorma100712, DescripcionDescuentooRecargo12, TipoValor12, ValorDescuentooRecargo12, 
                         MontoDescuentooRecargo12, MontoDescuentooRecargoOtraMoneda12, IndicadorFacturacionDescuentooRecargo12, NumeroLineaDoR13, TipoAjuste13, IndicadorNorma100713, DescripcionDescuentooRecargo13, TipoValor13, 
                         ValorDescuentooRecargo13, MontoDescuentooRecargo13, MontoDescuentooRecargoOtraMoneda13, IndicadorFacturacionDescuentooRecargo13, NumeroLineaDoR14, TipoAjuste14, IndicadorNorma100714, 
                         DescripcionDescuentooRecargo14, TipoValor14, ValorDescuentooRecargo14, MontoDescuentooRecargo14, MontoDescuentooRecargoOtraMoneda14, IndicadorFacturacionDescuentooRecargo14, NumeroLineaDoR15, 
                         TipoAjuste15, IndicadorNorma100715, DescripcionDescuentooRecargo15, TipoValor15, ValorDescuentooRecargo15, MontoDescuentooRecargo15, MontoDescuentooRecargoOtraMoneda15, 
                         IndicadorFacturacionDescuentooRecargo15, NumeroLineaDoR16, TipoAjuste16, IndicadorNorma100716, DescripcionDescuentooRecargo16, TipoValor16, ValorDescuentooRecargo16, MontoDescuentooRecargo16, 
                         MontoDescuentooRecargoOtraMoneda16, IndicadorFacturacionDescuentooRecargo16, NumeroLineaDoR17, TipoAjuste17, IndicadorNorma100717, DescripcionDescuentooRecargo17, TipoValor17, ValorDescuentooRecargo17, 
                         MontoDescuentooRecargo17, MontoDescuentooRecargoOtraMoneda17, IndicadorFacturacionDescuentooRecargo17, NumeroLineaDoR18, TipoAjuste18, IndicadorNorma100718, DescripcionDescuentooRecargo18, TipoValor18, 
                         ValorDescuentooRecargo18, MontoDescuentooRecargo18, MontoDescuentooRecargoOtraMoneda18, IndicadorFacturacionDescuentooRecargo18, NumeroLineaDoR19, TipoAjuste19, IndicadorNorma100719, 
                         DescripcionDescuentooRecargo19, TipoValor19, ValorDescuentooRecargo19, MontoDescuentooRecargo19, MontoDescuentooRecargoOtraMoneda19, IndicadorFacturacionDescuentooRecargo19, NumeroLineaDoR20, 
                         TipoAjuste20, IndicadorNorma100720, DescripcionDescuentooRecargo20, TipoValor20, ValorDescuentooRecargo20, MontoDescuentooRecargo20, MontoDescuentooRecargoOtraMoneda20, 
                         IndicadorFacturacionDescuentooRecargo20, NCFModificado, RNCOtroContribuyente, FechaNCFModificado, CodigoModificacion, RazonModificacion, IndicadorMontoGravadoI18, IndicadorMontoGravadoI16, 
                         IndicadorMontoGravadoI0, Tabla, campo1, campo2,
						 CASE
        WHEN SUBSTRING(eNCF, 2, 2) = '32' AND MontoTotal < 250000 
            THEN CONCAT(
                'https://fc.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbreFC?RncEmisor=', TRIM(rncemisor),
                '&ENCF=', TRIM(eNCF),
                '&MontoTotal=', MontoTotal,
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(CodigoSeguridad))
            )
        WHEN SUBSTRING(eNCF, 2, 2) = '47' 
            THEN CONCAT(
                'https://ecf.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbre?RncEmisor=', TRIM(rncemisor),
                '&ENCF=', TRIM(eNCF),
                '&FechaEmision=', dbo.FNFechaDMY(FechaEmision),
                '&MontoTotal=', MontoTotal,
                '&FechaFirma=', REPLACE(TRIM(FechaFirma), ' ', '%20'),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](CodigoSeguridad)
            )
        ELSE 
            CONCAT(
                'https://ecf.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbre?RncEmisor=', TRIM(rncemisor),
                '&RncComprador=', TRIM(RNCComprador),  --El origen del rnc cambia en cada cliente y base de datos
                '&ENCF=', TRIM(eNCF),
                '&FechaEmision=', dbo.FNFechaDMY(FechaEmision),
                '&MontoTotal=', MontoTotal,
                '&FechaFirma=', REPLACE(TRIM(FechaFirma), ' ', '%20'),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(CodigoSeguridad))
            )
    END AS URLQR


FROM            dbo.FEEncabezado
CROSS JOIN AmbienteInfo AI