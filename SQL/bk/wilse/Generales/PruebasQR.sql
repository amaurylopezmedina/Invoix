WITH 
e AS (SELECT   rnc, Ambiente
      FROM  dbo.empresa WITH (NOLOCK)), 
AmbienteInfo AS
    (SELECT   A.ambiente, A.descrip, ISNULL(A.ruta, '') AS RUTA
      FROM   dbo.FEAmbiente AS A WITH (NOLOCK) 
	  INNER JOIN  e AS e_1 ON A.ambiente = e_1.Ambiente)
  
   Select  CASE
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
    END AS URLQR from vFEEncabezado
	CROSS JOIN AmbienteInfo AI