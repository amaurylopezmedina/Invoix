SELECT estadofiscal,ncf, tipo FROM transa01 WHERE UPPER(LEFT(ncf, 3)) = 'E31' AND tipo IN ('03', '04');

update transa01 set estadofiscal=1, estadoimpresion = 1 and  ncf = '' WHERE UPPER(LEFT(ncf, 3)) = 'E31' AND tipo IN ('03', '04');

SELECT  ncf, tipo,
       LEFT(ncf, 3) AS prefijo,
       RIGHT(ncf, LEN(ncf) - 3) AS secuencia_actual,
       CAST(RIGHT(ncf, LEN(ncf) - 3) AS BIGINT) + 8 AS nueva_secuencia
FROM transa01
WHERE UPPER(LEFT(ncf, 3)) = 'E31'
AND tipo IN ('03', '04');


UPDATE transa01
SET ncf = 
    LEFT(ncf, 3) + 
    RIGHT(REPLICATE('0', LEN(ncf) - 3) + 
          CAST(CAST(RIGHT(ncf, LEN(ncf) - 3) AS BIGINT) + 8 AS VARCHAR(20)), 
          LEN(ncf) - 3)
WHERE UPPER(LEFT(ncf, 3)) = 'E31'
AND tipo IN ('03', '04');
