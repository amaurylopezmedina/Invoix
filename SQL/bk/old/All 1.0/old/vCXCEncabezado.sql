SELECT
  cxc.documento AS NumeroFacturaInterna,
  cxc.tipomovi AS TipoDocumento,
  SUBSTRING(cxc.ncf, 1, 1) AS TipoECFL,
  SUBSTRING(cxc.ncf, 2, 2) AS TipoECF,
  tn.Descripcion AS TipoECFL1,
  tn.Descripcion,
  tn.Auxiliar,
  tn.Tabla,
  tn.campo1,
  tn.campo2,
  cxc.ncf AS eNCF,
  cxc.FVencimientoNCF AS FechaVencimientoSecuencia,
  cxc.vence AS FechaLimitePago,
  cxc.dia AS TerminoPagoN,
  CAST(cxc.dia AS char (3)) + ' Dias' AS TerminoPago,
  cxc.ALMACEN,
  (
    CASE
      WHEN cxc.tipomovi = '03' THEN 1
      ELSE 0
    END
  ) AS IndicadorNotaCredito,
  (
    SELECT
      TOP(1) itbisenprecio
    FROM
      dbo.empresa AS e1
    WHERE
      (cxc.RNCEmisor = rnc)
  ) AS IndicadorMontoGravado,
  '01' AS TipoIngresos,
  (
    CASE
      WHEN cxc.tipomovi = '' THEN 1
      WHEN cxc.tipomovi = '03'
      OR cxc.tipomovi = '02' THEN 2
    END
  ) AS TipoPago,
  (
    CASE
      WHEN cxc.tipomovi = '' THEN 'Contado'
      WHEN cxc.tipomovi = '03'
      OR cxc.tipomovi = '02' THEN 'Crédito'
    END
  ) AS TipoPagoL,
  NULL AS TipoCuentaPago,
  NULL AS NumeroCuentaPago,
  NULL AS BancoPago,
  NULL AS FechaDesde,
  NULL AS FechaHasta,
  NULL AS TotalPaginas,
  REPLACE(cxc.RNCEmisor, '-', '') AS RNCEmisor,
  e.TipodeIngresos,
  e.IndicadorEnvioDiferido,
  e.RazonSocialEmisor,
  e.NombreComercial,
  e.Sucursal,
  e.DireccionEmisor,
  e.MunicipioFE AS Municipio,
  e.ProvinciaFE AS Provincia,
  e.CorreoEmisor,
  e.WebSite,
  e.ActividadEconomica,
  e.Tele AS TelefonoEmisor1,
  NULL AS TelefonoEmisor2,
  NULL AS TelefonoEmisor3,
  cxc.vendedor AS CodigoVendedor,
  NULL AS NumeroPedidoInterno,
  NULL AS ZonaVenta,
  NULL AS RutaVenta,
  NULL AS InformacionAdicionalEmisor,
  cxc.fecha AS FechaEmision,
  cl.rnc1 AS RNCComprador,
  NULL AS IdentificadorExtranjero,
  (
    CASE
      WHEN cl.cedula IS NOT NULL
      AND cl.cedula <> '' THEN cl.Nombre
      ELSE 'CLIENTE GENERICO'
    END
  ) AS RazonSocialComprador,
  cl.contacto AS ContactoComprador,
  cl.Email AS CorreoComprador,
  cl.Dire AS DireccionComprador,
  NULL AS MunicipioComprador,
  NULL AS ProvinciaComprador,
  NULL AS PaisComprador,
  NULL AS FechaEntrega,
  NULL AS ContactoEntrega,
  NULL AS DireccionEntrega,
  cl.Tele AS TelefonoAdicional,
  NULL AS FechaOrdenCompra,
  NULL AS NumeroOrdenCompra,
  cxc.cliente AS CodigoInternoComprador,
  NULL AS ResponsablePago,
  NULL AS Informacionadicionalcomprador,
  NULL AS FechaEmbarque,
  NULL AS NumeroEmbarque,
  NULL AS NumeroContenedor,
  NULL AS NumeroReferencia,
  NULL AS NombrePuertoEmbarque,
  NULL AS CondicionesEntrega,
  NULL AS TotalFob,
  NULL AS Seguro,
  NULL AS Flete,
  NULL AS OtrosGastos,
  NULL AS TotalCif,
  NULL AS RegimenAduanero,
  NULL AS NombrePuertoSalida,
  NULL AS NombrePuertoDesembarque,
  NULL AS PesoBruto,
  NULL AS PesoNeto,
  NULL AS UnidadPesoBruto,
  NULL AS UnidadPesoNeto,
  NULL AS CantidadBulto,
  NULL AS UnidadBulto,
  NULL AS VolumenBulto,
  NULL AS UnidadVolumen,
  NULL AS ViaTransporte,
  NULL AS PaisOrigen,
  NULL AS DireccionDestino,
  NULL AS PaisDestino,
  NULL AS RNCIdentificacionCompaniaTransportista,
  NULL AS NombreCompaniaTransportista,
  NULL AS NumeroViaje,
  NULL AS Conductor,
  NULL AS DocumentoTransporte,
  NULL AS Ficha,
  NULL AS Placa,
  NULL AS RutaTransporte,
  NULL AS ZonaTransporte,
  NULL AS NumeroAlbaran,
  td_1.MontoGravadoTotal,
  td_1.MontoGravadoI1,
  td_1.MontoGravadoI2,
  td_1.MontoGravadoI3,
  td_1.MontoExento,
  td_1.ITBIS1,
  td_1.ITBIS2,
  td_1.ITBIS3,
  td_1.TotalITBIS,
  td_1.TotalITBIS1,
  td_1.TotalITBIS2,
  td_1.TotalITBIS3,
  td_1.IndicadorMontoGRabadoI18,
  td_1.IndicadorMontoGRabadoI16,
  td_1.IndicadorMontoGRabadoI0,
  NULL AS MontoImpuestoAdicional,
  NULL AS TipoImpuesto1,
  NULL AS TasaImpuestoAdicional1,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico1,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem1,
  NULL AS OtrosImpuestosAdicionales1,
  NULL AS TipoImpuesto2,
  NULL AS TasaImpuestoAdicional2,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico2,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem2,
  NULL AS OtrosImpuestosAdicionales2,
  NULL AS TipoImpuesto3,
  NULL AS TasaImpuestoAdicional3,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico3,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem3,
  NULL AS OtrosImpuestosAdicionales3,
  NULL AS TipoImpuesto4,
  NULL AS TasaImpuestoAdicional4,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico4,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem4,
  NULL AS OtrosImpuestosAdicionales4,
  NULL AS TipoImpuesto5,
  NULL AS TasaImpuestoAdicional5,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico5,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem5,
  NULL AS OtrosImpuestosAdicionales5,
  NULL AS TipoImpuesto6,
  NULL AS TasaImpuestoAdicional6,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico6,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem6,
  NULL AS OtrosImpuestosAdicionales6,
  NULL AS TipoImpuesto7,
  NULL AS TasaImpuestoAdicional7,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico7,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem7,
  NULL AS OtrosImpuestosAdicionales7,
  NULL AS TipoImpuesto8,
  NULL AS TasaImpuestoAdicional8,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico8,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem8,
  NULL AS OtrosImpuestosAdicionales8,
  NULL AS TipoImpuesto9,
  NULL AS TasaImpuestoAdicional9,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico9,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem9,
  NULL AS OtrosImpuestosAdicionales9,
  NULL AS TipoImpuesto10,
  NULL AS TasaImpuestoAdicional10,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico10,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem10,
  NULL AS OtrosImpuestosAdicionales10,
  NULL AS TipoImpuesto11,
  NULL AS TasaImpuestoAdicional11,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico11,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem11,
  NULL AS OtrosImpuestosAdicionales11,
  NULL AS TipoImpuesto12,
  NULL AS TasaImpuestoAdicional12,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico12,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem12,
  NULL AS OtrosImpuestosAdicionales12,
  NULL AS TipoImpuesto13,
  NULL AS TasaImpuestoAdicional13,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico13,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem13,
  NULL AS OtrosImpuestosAdicionales13,
  NULL AS TipoImpuesto14,
  NULL AS TasaImpuestoAdicional14,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico14,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem14,
  NULL AS OtrosImpuestosAdicionales14,
  NULL AS TipoImpuesto15,
  NULL AS TasaImpuestoAdicional15,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico15,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem15,
  NULL AS OtrosImpuestosAdicionales15,
  NULL AS TipoImpuesto16,
  NULL AS TasaImpuestoAdicional16,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico16,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem16,
  NULL AS OtrosImpuestosAdicionales16,
  NULL AS TipoImpuesto17,
  NULL AS TasaImpuestoAdicional17,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico17,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem17,
  NULL AS OtrosImpuestosAdicionales17,
  NULL AS TipoImpuesto18,
  NULL AS TasaImpuestoAdicional18,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico18,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem18,
  NULL AS OtrosImpuestosAdicionales18,
  NULL AS TipoImpuesto19,
  NULL AS TasaImpuestoAdicional19,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico19,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem19,
  NULL AS OtrosImpuestosAdicionales19,
  NULL AS TipoImpuesto20,
  NULL AS TasaImpuestoAdicional20,
  NULL AS MontoImpuestoSelectivoConsumoEspecifico20,
  NULL AS MontoImpuestoSelectivoConsumoAdvalorem20,
  NULL AS OtrosImpuestosAdicionales20,
  NULL AS asNumeroLineaDoR1,
  NULL AS asTipoAjuste1,
  NULL AS asIndicadorNorma10071,
  NULL AS asDescripcionDescuentooRecargo1,
  NULL AS asTipoValor1,
  NULL AS asValorDescuentooRecargo1,
  NULL AS NumeroLineaDoR1,
  NULL AS TipoAjuste1,
  NULL AS IndicadorNorma10071,
  NULL AS DescripcionDescuentooRecargo1,
  NULL AS TipoValor1,
  NULL AS ValorDescuentooRecargo1,
  NULL AS MontoDescuentooRecargo1,
  NULL AS MontoDescuentooRecargoOtraMoneda1,
  NULL AS IndicadorFacturacionDescuentooRecargo1,
  NULL AS NumeroLineaDoR2,
  NULL AS TipoAjuste2,
  NULL AS IndicadorNorma10072,
  NULL AS DescripcionDescuentooRecargo2,
  NULL AS TipoValor2,
  NULL AS ValorDescuentooRecargo2,
  NULL AS MontoDescuentooRecargo2,
  NULL AS MontoDescuentooRecargoOtraMoneda2,
  NULL AS IndicadorFacturacionDescuentooRecargo2,
  NULL AS NumeroLineaDoR3,
  NULL AS TipoAjuste3,
  NULL AS IndicadorNorma10073,
  NULL AS DescripcionDescuentooRecargo3,
  NULL AS TipoValor3,
  NULL AS ValorDescuentooRecargo3,
  NULL AS MontoDescuentooRecargo3,
  NULL AS MontoDescuentooRecargoOtraMoneda3,
  NULL AS IndicadorFacturacionDescuentooRecargo3,
  NULL AS NumeroLineaDoR4,
  NULL AS TipoAjuste4,
  NULL AS IndicadorNorma10074,
  NULL AS DescripcionDescuentooRecargo4,
  NULL AS TipoValor4,
  NULL AS ValorDescuentooRecargo4,
  NULL AS MontoDescuentooRecargo4,
  NULL AS MontoDescuentooRecargoOtraMoneda4,
  NULL AS IndicadorFacturacionDescuentooRecargo4,
  NULL AS NumeroLineaDoR5,
  NULL AS TipoAjuste5,
  NULL AS IndicadorNorma10075,
  NULL AS DescripcionDescuentooRecargo5,
  NULL AS TipoValor5,
  NULL AS ValorDescuentooRecargo5,
  NULL AS MontoDescuentooRecargo5,
  NULL AS MontoDescuentooRecargoOtraMoneda5,
  NULL AS IndicadorFacturacionDescuentooRecargo5,
  NULL AS NumeroLineaDoR6,
  NULL AS TipoAjuste6,
  NULL AS IndicadorNorma10076,
  NULL AS DescripcionDescuentooRecargo6,
  NULL AS TipoValor6,
  NULL AS ValorDescuentooRecargo6,
  NULL AS MontoDescuentooRecargo6,
  NULL AS MontoDescuentooRecargoOtraMoneda6,
  NULL AS IndicadorFacturacionDescuentooRecargo6,
  NULL AS NumeroLineaDoR7,
  NULL AS TipoAjuste7,
  NULL AS IndicadorNorma10077,
  NULL AS DescripcionDescuentooRecargo7,
  NULL AS TipoValor7,
  NULL AS ValorDescuentooRecargo7,
  NULL AS MontoDescuentooRecargo7,
  NULL AS MontoDescuentooRecargoOtraMoneda7,
  NULL AS IndicadorFacturacionDescuentooRecargo7,
  NULL AS NumeroLineaDoR8,
  NULL AS TipoAjuste8,
  NULL AS IndicadorNorma10078,
  NULL AS DescripcionDescuentooRecargo8,
  NULL AS TipoValor8,
  NULL AS ValorDescuentooRecargo8,
  NULL AS MontoDescuentooRecargo8,
  NULL AS MontoDescuentooRecargoOtraMoneda8,
  NULL AS IndicadorFacturacionDescuentooRecargo8,
  NULL AS NumeroLineaDoR9,
  NULL AS TipoAjuste9,
  NULL AS IndicadorNorma10079,
  NULL AS DescripcionDescuentooRecargo9,
  NULL AS TipoValor9,
  NULL AS ValorDescuentooRecargo9,
  NULL AS MontoDescuentooRecargo9,
  NULL AS MontoDescuentooRecargoOtraMoneda9,
  NULL AS IndicadorFacturacionDescuentooRecargo9,
  NULL AS NumeroLineaDoR10,
  NULL AS TipoAjuste10,
  NULL AS IndicadorNorma100710,
  NULL AS DescripcionDescuentooRecargo10,
  NULL AS TipoValor10,
  NULL AS ValorDescuentooRecargo10,
  NULL AS MontoDescuentooRecargo10,
  NULL AS MontoDescuentooRecargoOtraMoneda10,
  NULL AS IndicadorFacturacionDescuentooRecargo10,
  NULL AS NumeroLineaDoR11,
  NULL AS TipoAjuste11,
  NULL AS IndicadorNorma100711,
  NULL AS DescripcionDescuentooRecargo11,
  NULL AS TipoValor11,
  NULL AS ValorDescuentooRecargo11,
  NULL AS MontoDescuentooRecargo11,
  NULL AS MontoDescuentooRecargoOtraMoneda11,
  NULL AS IndicadorFacturacionDescuentooRecargo11,
  NULL AS NumeroLineaDoR12,
  NULL AS TipoAjuste12,
  NULL AS IndicadorNorma100712,
  NULL AS DescripcionDescuentooRecargo12,
  NULL AS TipoValor12,
  NULL AS ValorDescuentooRecargo12,
  NULL AS MontoDescuentooRecargo12,
  NULL AS MontoDescuentooRecargoOtraMoneda12,
  NULL AS IndicadorFacturacionDescuentooRecargo12,
  NULL AS NumeroLineaDoR13,
  NULL AS TipoAjuste13,
  NULL AS IndicadorNorma100713,
  NULL AS DescripcionDescuentooRecargo13,
  NULL AS TipoValor13,
  NULL AS ValorDescuentooRecargo13,
  NULL AS MontoDescuentooRecargo13,
  NULL AS MontoDescuentooRecargoOtraMoneda13,
  NULL AS IndicadorFacturacionDescuentooRecargo13,
  NULL AS NumeroLineaDoR14,
  NULL AS TipoAjuste14,
  NULL AS IndicadorNorma100714,
  NULL AS DescripcionDescuentooRecargo14,
  NULL AS TipoValor14,
  NULL AS ValorDescuentooRecargo14,
  NULL AS MontoDescuentooRecargo14,
  NULL AS MontoDescuentooRecargoOtraMoneda14,
  NULL AS IndicadorFacturacionDescuentooRecargo14,
  NULL AS NumeroLineaDoR15,
  NULL AS TipoAjuste15,
  NULL AS IndicadorNorma100715,
  NULL AS DescripcionDescuentooRecargo15,
  NULL AS TipoValor15,
  NULL AS ValorDescuentooRecargo15,
  NULL AS MontoDescuentooRecargo15,
  NULL AS MontoDescuentooRecargoOtraMoneda15,
  NULL AS IndicadorFacturacionDescuentooRecargo15,
  NULL AS NumeroLineaDoR16,
  NULL AS TipoAjuste16,
  NULL AS IndicadorNorma100716,
  NULL AS DescripcionDescuentooRecargo16,
  NULL AS TipoValor16,
  NULL AS ValorDescuentooRecargo16,
  NULL AS MontoDescuentooRecargo16,
  NULL AS MontoDescuentooRecargoOtraMoneda16,
  NULL AS IndicadorFacturacionDescuentooRecargo16,
  NULL AS NumeroLineaDoR17,
  NULL AS TipoAjuste17,
  NULL AS IndicadorNorma100717,
  NULL AS DescripcionDescuentooRecargo17,
  NULL AS TipoValor17,
  NULL AS ValorDescuentooRecargo17,
  NULL AS MontoDescuentooRecargo17,
  NULL AS MontoDescuentooRecargoOtraMoneda17,
  NULL AS IndicadorFacturacionDescuentooRecargo17,
  NULL AS NumeroLineaDoR18,
  NULL AS TipoAjuste18,
  NULL AS IndicadorNorma100718,
  NULL AS DescripcionDescuentooRecargo18,
  NULL AS TipoValor18,
  NULL AS ValorDescuentooRecargo18,
  NULL AS MontoDescuentooRecargo18,
  NULL AS MontoDescuentooRecargoOtraMoneda18,
  NULL AS IndicadorFacturacionDescuentooRecargo18,
  NULL AS NumeroLineaDoR19,
  NULL AS TipoAjuste19,
  NULL AS IndicadorNorma100719,
  NULL AS DescripcionDescuentooRecargo19,
  NULL AS TipoValor19,
  NULL AS ValorDescuentooRecargo19,
  NULL AS MontoDescuentooRecargo19,
  NULL AS MontoDescuentooRecargoOtraMoneda19,
  NULL AS IndicadorFacturacionDescuentooRecargo19,
  NULL AS NumeroLineaDoR20,
  NULL AS TipoAjuste20,
  NULL AS IndicadorNorma100720,
  NULL AS DescripcionDescuentooRecargo20,
  NULL AS TipoValor20,
  NULL AS ValorDescuentooRecargo20,
  NULL AS MontoDescuentooRecargo20,
  NULL AS MontoDescuentooRecargoOtraMoneda20,
  NULL AS IndicadorFacturacionDescuentooRecargo20,
  NULL AS NombreVendedor,
  (
    CASE
      WHEN COALESCE(cxc.tasa, 0.00) = 0 THEN cxc.monto * 1
      ELSE cxc.monto * cxc.tasa
    END
  ) AS MontoTotal,
  NULL AS MontoNoFacturable,
  NULL AS MontoPeriodo,
  NULL AS SaldoAnterior,
  NULL AS MontoAvancePago,
  (
    CASE
      WHEN COALESCE(cxc.tasa, 0.00) = 0 THEN cxc.monto * 1
      ELSE cxc.monto * cxc.tasa
    END
  ) AS MontoPago,
  (
    CASE
      WHEN COALESCE(cxc.tasa, 0.00) = 0 THEN cxc.monto * 1
      ELSE cxc.monto * cxc.tasa
    END
  ) AS ValorPagar,
  NULL AS TotalITBISRetenido,
  NULL AS TotalISRRetencion,
  NULL AS TotalITBISPercepcion,
  NULL AS TotalISRPercepcion,
  (
    CASE
      WHEN cxc.tipomovi = '' THEN 'USD'
      WHEN cxc.tipomovi = '03'
      OR cxc.tipomovi = '02' THEN 'DOP'
      ELSE 'DOP'
    END
  ) AS TipoMoneda,
  (
    CASE
      WHEN cxc.tipomovi = '' THEN 'DOLAR ESTADOUNIDENSE'
      WHEN cxc.tipomovi = '03'
      OR cxc.tipomovi = '02' THEN 'PESO DOMINICANO'
      ELSE 'PESO DOMINICANO'
    END
  ) AS TipoMonedaL,
  COALESCE(cxc.tasa, 0.00) AS TipoCambio,
  td_1.MontoGravadoTotalOtraMoneda,
  td_1.MontoGravadoI1OtraMoneda,
  td_1.MontoGravadoI2OtraMoneda,
  td_1.MontoGravadoI3OtraMoneda,
  td_1.MontoExentoOtraMoneda,
  td_1.TotalITBISOtraMoneda,
  td_1.TotalITBIS1OtraMoneda,
  td_1.TotalITBIS2OtraMoneda,
  td_1.TotalITBIS3OtraMoneda,
  NULL AS MontoImpuestoAdicionalOtraMoneda,
  (
    CASE
      WHEN COALESCE(cxc.tasa, 0.00) = 0 THEN 0
      ELSE cxc.monto
    END
  ) AS MontoTotalOtraMoneda,
  cxc.Documento1 AS NCFModificado,
  NULL AS FechaNCFModificado,
  NULL AS CodigoModificacion,
  cxc.concepto AS RazonModificacion,
  cxc.fechacreacion,
  cxc.Trackid,
  cxc.FechaFirma,
  cxc.CodigoSeguridad,
  cxc.Estadoimpresion,
  NULL AS ConteoImpresiones,
  cxc.EstadoFiscal,
  CASE
    WHEN RIGHT(cxc.ncf, 2) = '32'
    AND cxc.monto < 250000 THEN CONCAT(
      'https://fc.dgii.gov.do/ecf/ConsultaTimbreFC?RncEmisor=',
      TRIM(cxc.rncemisor),
      '&ENCF=',
      TRIM(cxc.ncf),
      '&MontoTotal=',
      cxc.monto,
      '&CodigoSeguridad=',
      [dbo].[FNCambiaHexadecimal] (TRIM(cxc.CodigoSeguridad))
    )
    WHEN RIGHT(cxc.ncf, 2) = '47' THEN CONCAT(
      'https://ecf.dgii.gov.do/ecf/ConsultaTimbre?RncEmisor=',
      TRIM(cxc.rncemisor),
      '&ENCF=',
      TRIM(cxc.ncf),
      '&FechaEmision=',
      dbo.FNFechaDMY (cxc.fecha),
      '&MontoTotal=',
      cxc.monto,
      '&FechaFirma=',
      REPLACE(TRIM(cxc.FechaFirma), ' ', '%20'),
      '&CodigoSeguridad=',
      [dbo].[FNCambiaHexadecimal] (cxc.CodigoSeguridad)
    )
    ELSE CONCAT(
      'https://ecf.dgii.gov.do/ecf/ConsultaTimbre?RncEmisor=',
      TRIM(cxc.rncemisor),
      '&RncComprador=',
      TRIM(cl.rnc1),
      '&ENCF=',
      TRIM(cxc.ncf),
      '&FechaEmision=',
      dbo.FNFechaDMY (cxc.fecha),
      '&MontoTotal=',
      cxc.monto,
      '&FechaFirma=',
      REPLACE(TRIM(cxc.FechaFirma), ' ', '%20'),
      '&CodigoSeguridad=',
      [dbo].[FNCambiaHexadecimal] (TRIM(cxc.CodigoSeguridad))
    )
  END AS URLQR,
  NULL AS Observaciones,
  cxc.creado AS Creadopor,
  NULL AS ModificadoPor,
  NULL AS NotaPermanente
FROM
  dbo.cxcmovi1 AS cxc
  LEFT OUTER JOIN dbo.sis_TipoNCF AS tn ON tn.Codigo = SUBSTRING(cxc.ncf, 2, 2)
  LEFT OUTER JOIN dbo.empresa AS e ON cxc.RNCEmisor = e.rnc
  LEFT OUTER JOIN dbo.cliente AS cl ON cl.cliente = cxc.cliente
  LEFT OUTER JOIN (
    SELECT
      td.numero,
      td.fecha,
      td.tipo,
      cxc.RNCEmisor,
      cxc.ncf,
      COALESCE(cxc.tasa, 1.00) AS tasa,
      td.itbis,
      (
        SELECT
          itbisenprecio
        FROM
          dbo.empresa AS e1
        WHERE
          (cxc.RNCEmisor = rnc)
      ) AS IndicadorMontoGravado,
      (
        CASE
          WHEN (
            SELECT
              itbisenprecio
            FROM
              dbo.empresa AS e1
            WHERE
              (cxc.RNCEmisor = e1.rnc)
          ) = 0 THEN SUM(
            CASE
              WHEN td.itbis <> 0 THEN (
                CASE
                  WHEN COALESCE(cxc.tasa, 1.00) = 1 THEN td.monto1 * 1
                  ELSE td.monto1 * cxc.tasa
                END
              )
              ELSE 0.00
            END
          )
          WHEN (
            SELECT
              itbisenprecio
            FROM
              dbo.empresa AS e1
            WHERE
              (cxc.RNCEmisor = e1.rnc)
          ) = 1 THEN SUM(
            CASE
              WHEN td.itbis <> 0 THEN (
                CASE
                  WHEN COALESCE(cxc.tasa, 1.00) = 1 THEN td.monto1 * 1
                  ELSE td.monto1 * cxc.tasa
                END
              )
              ELSE 0.00
            END
          ) - SUM(
            CASE
              WHEN COALESCE(cxc.tasa, 1.00) = 1 THEN td.montoitbis * 1
              ELSE td.montoitbis * cxc.tasa
            END
          )
        END
      ) AS MontoGravadoTotal,
      (
        CASE
          WHEN (
            SELECT
              itbisenprecio
            FROM
              dbo.empresa AS e1
            WHERE
              (cxc.RNCEmisor = e1.rnc)
          ) = 0
          AND td.itbis = 18 THEN SUM(
            CASE
              WHEN td.itbis = 18 THEN (
                CASE
                  WHEN COALESCE(cxc.tasa, 1.00) = 1 THEN td.monto1 * 1
                  ELSE td.monto1 * cxc.tasa
                END
              )
              ELSE 0.00
            END
          )
          WHEN (
            SELECT
              itbisenprecio
            FROM
              dbo.empresa AS e1
            WHERE
              (cxc.RNCEmisor = e1.rnc)
          ) = 1
          AND td.itbis = 18 THEN SUM(
            CASE
              WHEN td.itbis = 18 THEN (
                CASE
                  WHEN COALESCE(cxc.tasa, 1.00) = 1 THEN td.monto1 * 1
                  ELSE td.monto1 * cxc.tasa
                END
              )
              ELSE 0.00
            END
          ) - SUM(
            CASE
              WHEN COALESCE(cxc.tasa, 1.00) = 1 THEN td.montoitbis * 1
              ELSE td.montoitbis * cxc.tasa
            END
          )
          ELSE 0.00
        END
      ) AS MontoGravadoI1,
      (
        CASE
          WHEN (
            SELECT
              itbisenprecio
            FROM
              dbo.empresa AS e1
            WHERE
              (cxc.RNCEmisor = e1.rnc)
          ) = 0
          AND td.itbis = 16 THEN SUM(
            CASE
              WHEN td.itbis = 16 THEN (
                CASE
                  WHEN COALESCE(cxc.tasa, 1.00) = 1 THEN td.monto1 * 1
                  ELSE td.monto1 * cxc.tasa
                END
              )
              ELSE 0.00
            END
          )
          WHEN (
            SELECT
              itbisenprecio
            FROM
              dbo.empresa AS e1
            WHERE
              (cxc.RNCEmisor = e1.rnc)
          ) = 1
          AND td.itbis = 16 THEN SUM(
            CASE
              WHEN td.itbis = 16 THEN (
                CASE
                  WHEN COALESCE(cxc.tasa, 1.00) = 1 THEN td.monto1 * 1
                  ELSE td.monto1 * cxc.tasa
                END
              )
              ELSE 0.00
            END
          ) - SUM(
            CASE
              WHEN COALESCE(cxc.tasa, 1.00) = 1 THEN td.montoitbis * 1
              ELSE td.montoitbis * cxc.tasa
            END
          )
          ELSE 0.00
        END
      ) AS MontoGravadoI2,
      SUM(
        CASE
          WHEN td.itbis = 0 THEN 0.00
          ELSE 0.00
        END
      ) AS MontoGravadoI3,
      SUM(
        CASE
          WHEN td.itbis = 0 THEN (
            CASE
              WHEN COALESCE(cxc.tasa, 1.00) = 1 THEN td.monto1 * COALESCE(cxc.tasa, 1.00)
              ELSE td.monto1 * cxc.tasa
            END
          )
          ELSE NULL
        END
      ) AS MontoExento,
      MAX(
        CASE
          WHEN td.itbis = 18 THEN td.itbis
          ELSE NULL
        END
      ) AS ITBIS1,
      MAX(
        CASE
          WHEN td.itbis = 16 THEN td.itbis
          ELSE NULL
        END
      ) AS ITBIS2,
      MAX(
        CASE
          WHEN td.itbis = 0 THEN td.itbis
          ELSE NULL
        END
      ) AS ITBIS3,
      SUM(
        (
          CASE
            WHEN COALESCE(cxc.tasa, 1) = 1 THEN td.montoitbis * COALESCE(cxc.tasa, 1)
            ELSE td.montoitbis * cxc.tasa
          END
        )
      ) AS TotalITBIS,
      SUM(
        CASE
          WHEN td.itbis = 18 THEN td.montoitbis * COALESCE(cxc.tasa, 1)
          ELSE NULL
        END
      ) AS TotalITBIS1,
      SUM(
        CASE
          WHEN td.itbis = 16 THEN td.montoitbis * COALESCE(cxc.tasa, 1)
          ELSE NULL
        END
      ) AS TotalITBIS2,
      SUM(
        CASE
          WHEN td.itbis = 0 THEN 0
          ELSE NULL
        END
      ) AS TotalITBIS3,
      MAX(
        CASE
          WHEN td.itbis = 18 THEN 1
          ELSE 0
        END
      ) AS IndicadorMontoGRabadoI18,
      MAX(
        CASE
          WHEN td.itbis = 16 THEN 1
          ELSE 0
        END
      ) AS IndicadorMontoGRabadoI16,
      MAX(
        CASE
          WHEN td.itbis = 0 THEN 1
          ELSE 0
        END
      ) AS IndicadorMontoGRabadoI0,
      SUM(
        CASE
          WHEN td.itbis <> 0 THEN (
            CASE
              WHEN COALESCE(cxc.tasa, 1.00) = 1 THEN 1
              ELSE td.monto1
            END
          )
          ELSE 0.00
        END
      ) AS MontoGravadoTotalOtraMoneda,
      SUM(
        CASE
          WHEN td.itbis = 18 THEN (
            CASE
              WHEN COALESCE(cxc.tasa, 1.00) = 1 THEN 1
              ELSE td.monto1
            END
          )
          ELSE 0.00
        END
      ) AS MontoGravadoI1OtraMoneda,
      SUM(
        CASE
          WHEN td.itbis = 16 THEN (
            CASE
              WHEN COALESCE(cxc.tasa, 1.00) = 1 THEN 1
              ELSE td.monto1
            END
          )
          ELSE 0.00
        END
      ) AS MontoGravadoI2OtraMoneda,
      SUM(
        CASE
          WHEN td.itbis = 0 THEN 0
          ELSE 0
        END
      ) AS MontoGravadoI3OtraMoneda,
      SUM(
        CASE
          WHEN td.itbis = 0 THEN (
            CASE
              WHEN COALESCE(cxc.tasa, 0.00) = 0 THEN 0
              ELSE td.monto1
            END
          )
          ELSE 0.00
        END
      ) AS MontoExentoOtraMoneda,
      SUM(
        (
          CASE
            WHEN COALESCE(cxc.tasa, 1.00) = 1 THEN 0
            ELSE td.montoitbis
          END
        )
      ) AS TotalITBISOtraMoneda,
      SUM(
        CASE
          WHEN td.itbis = 18 THEN (
            CASE
              WHEN COALESCE(cxc.tasa, 1.00) = 1 THEN 0
              ELSE td.montoitbis
            END
          )
          ELSE 0.00
        END
      ) AS TotalITBIS1OtraMoneda,
      SUM(
        CASE
          WHEN td.itbis = 16 THEN (
            CASE
              WHEN COALESCE(cxc.tasa, 1.00) = 1 THEN 0
              ELSE td.montoitbis
            END
          )
          ELSE 0.00
        END
      ) AS TotalITBIS2OtraMoneda,
      SUM(
        CASE
          WHEN td.itbis = 0 THEN 0
          ELSE 0.00
        END
      ) AS TotalITBIS3OtraMoneda
    FROM
      dbo.tradetalle AS td
      LEFT OUTER JOIN dbo.cxcmovi1 AS cxc ON cxc.documento = td.numero
      AND td.tipo = '05'
      AND cxc.tipomovi = '03'
    WHERE
      (cxc.EstadoFiscal IS NOT NULL)
    GROUP BY
      td.numero,
      td.fecha,
      td.tipo,
      cxc.RNCEmisor,
      cxc.ncf,
      COALESCE(cxc.tasa, 1.00),
      td.itbis
  ) AS td_1 ON td_1.numero = cxc.documento
  AND td_1.tipo = '05'
  AND cxc.tipomovi = '03'
WHERE
  (cxc.tipomovi IN ('03', '02'))
  AND (cxc.ncf IS NOT NULL)
  AND (cxc.ncf <> '')
  AND (cxc.EstadoFiscal IS NOT NULL)
