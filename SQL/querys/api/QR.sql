    
	WITH
 e AS (
    SELECT top 1
      itbisenprecio,
      trim(rnc)   as rnc ,
	  ambiente,
	  nota
    FROM empresa WITH (NOLOCK)
  ), 
 AmbienteInfo AS ( Select top 1
        A.AMBIENTE   as AMBIENTE, 
        A.DESCRIP   as DESCRIP, 
        ISNULL(A.RUTA, '')  AS RUTA 
    FROM FEAmbiente A WITH (NOLOCK)
	LEFT JOIN e WITH (NOLOCK) on  a.ambiente = e.ambiente 
    WHERE A.RUTA IS NOT NULL
	and a.ambiente = e.ambiente
)

	Select CASE
        WHEN SUBSTRING(enc.encf, 2, 2) = '32' AND enc.montototal < 250000 
            THEN CONCAT(
                'https://fc.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbreFC?RncEmisor=', TRIM(enc.rncemisor),
                '&ENCF=', TRIM(enc.encf),
                '&MontoTotal=', round(enc.montototal,2),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(enc.CodigoSeguridad))
            )
        WHEN SUBSTRING(enc.encf, 2, 2) = '47' 
            THEN CONCAT(
                'https://ecf.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbre?RncEmisor=', TRIM(enc.rncemisor),
                '&ENCF=', TRIM(enc.encf),
                '&FechaEmision=', dbo.FNFechaDMY(enc.fechaemision),
                '&MontoTotal=', round(enc.montototal,2),
                '&FechaFirma=', REPLACE(TRIM(enc.fechaFirma), ' ', '%20'),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](enc.CodigoSeguridad)
            )
        ELSE 
            CONCAT(
                'https://ecf.dgii.gov.do', 
                CASE WHEN LEN(TRIM(AI.ruta)) > 0 THEN CONCAT(TRIM(AI.ruta), '/') ELSE '' END,
                'ConsultaTimbre?RncEmisor=', TRIM(enc.rncemisor),
			    CONCAT('&RncComprador=', REPLACE(TRIM(enc.rnccomprador), '-', '')),
				'&ENCF=', TRIM(enc.encf),
                '&FechaEmision=', dbo.FNFechaDMY(enc.fechaemision),
                '&MontoTotal=', round(enc.montototal,2),
                '&FechaFirma=', REPLACE(TRIM(enc.FechaFirma), ' ', '%20'),
                '&CodigoSeguridad=', [dbo].[FNCambiaHexadecimal](TRIM(enc.CodigoSeguridad))
            )
    END  AS URLQR  
	from vfeencabezado enc
	  CROSS JOIN AmbienteInfo AS AI  WITH (NOLOCK)