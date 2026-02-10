SELECT  
--URL Necesrio para construnir el QR PARA impresion del Documento
(
    CASE
      WHEN TipoECF = '32'
      AND MontoTotal < 250000 THEN CONCAT(
        'https://fc.dgii.gov.do/testecf/ConsultaTimbreFC?RncEmisor=',
        TRIM(RNCEmisor),
        '&ENCF=',
        TRIM(eNCF),
        '&MontoTotal=',
        MontoTotal,
        '&CodigoSeguridad=',
        [dbo].[FNCambiaHexadecimal] (TRIM(CodigoSeguridad))
      )
      WHEN TipoECF = '47' THEN CONCAT(
        'https://ecf.dgii.gov.do/TesteCF/ConsultaTimbre?RncEmisor=',
        TRIM(RNCEmisor),
        '&ENCF=',
        TRIM(eNCF),
        '&FechaEmision=',
        dbo.FNFechaDMY (FechaEmision),
        '&MontoTotal=',
        MontoTotal,
        '&FechaFirma=',
        REPLACE(TRIM(FechaFirma), ' ', '%20'),
        '&CodigoSeguridad=',
        [dbo].[FNCambiaHexadecimal] (TRIM(CodigoSeguridad))
      )
      ELSE CONCAT(
        'https://ecf.dgii.gov.do/TesteCF/ConsultaTimbre?RncEmisor=',
        TRIM(RNCEmisor),
        '&RncComprador=',
        TRIM(RNCComprador),
        '&ENCF=',
        TRIM(eNCF),
        '&FechaEmision=',
        dbo.FNFechaDMY (FechaEmision),
        '&MontoTotal=',
        MontoTotal,
        '&FechaFirma=',
        REPLACE(TRIM(FechaFirma), ' ', '%20'),
        '&CodigoSeguridad=',
        [dbo].[FNCambiaHexadecimal] (TRIM(CodigoSeguridad))
      )
    END
  )  AS URLQR
FROM
  vFEEncabezado
WHERE
  eNCF = 'E340000000004'
