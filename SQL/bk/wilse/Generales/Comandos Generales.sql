
/*
update transa01 set   estadoimpresion=1 where       estadofiscal is not null --where ncf ='E340000000190      '    
update cxPmovi1 set estadofiscal=100, estadoimpresion=1 /*where  estadofiscal  is not null --*/ where  ncf = 'B0100015173' --estadofiscal =1  
update transa01 set estadofiscal=77, estadoimpresion=1  WHERE estadofiscal is not null  TIPOMOVI ='02' AND FECHA = '20250226'    estadofiscal is not null --where  estadofiscal=4 
update cxCmovi2 set estadofiscal=1, estadoimpresion=1 where   TIPOMOVI ='02' AND FECHA = '20250226' --where  estadofiscal=1 
update cajachica set estadofiscal=1, estadoimpresion=1 where estadofiscal  is not null --where  estadofiscal=1
*/

/*
alter table  cxCmovi1 add ResultadoEstadoFiscal text, MontoITBISDGII numeric(18,2), MontoDGII numeric(18,2)
alter table  cxPmovi1 add ResultadoEstadoFiscal text, MontoITBISDGII numeric(18,2), MontoDGII numeric(18,2)
alter table  cxcmovi2 add ResultadoEstadoFiscal text, MontoITBISDGII numeric(18,2), MontoDGII numeric(18,2)
alter table  cxCmovi1 add ResultadoEstadoFiscal text, MontoITBISDGII numeric(18,2), MontoDGII numeric(18,2)
alter table  cajachica add ResultadoEstadoFiscal text, MontoITBISDGII numeric(18,2), MontoDGII numeric(18,2)
*/
Select tIPOcAMBIO,IndicadorMontoGravado,MontoExento,MontoGravadoTotal,TABLA,RNCEmisor,MontoTotal,EstadoFiscal,Estadoimpresion,NumeroFacturaInterna,encf,NCFModificado,NumeroDocumentoNCFModificado,* from vFEEncabezado WHERE ESTADOFISCAL is not null    order by fechacreacion desc



Select * from transa01 where  tipoecf = 32 and MontoTotal < 250000

Select count(estadofiscal) from cxcmovi1 where fechacreacion is not null
Select count(estadofiscal) from cxcmovi1 where fechacreacion is null

Select count(estadofiscal) from cxcmovi1 

update  set estadofiscal = null, estadoimpresion = null where estadofiscal is not null



Select * from cxcmovi1 WHERE TIPOMOVI ='04' AND FECHA = '20250226'



ALTER SEQUENCE E34 RESTART WITH 177
SELECT NEXT VALUE FOR E34


update transa01 set ncf= 'E340000000177',estadofiscal=1, estadoimpresion=1  where ncf = 'E340000000005'    

--update transa01 set ncf= 'E460000003000',estadofiscal=1, estadoimpresion=1  where ncf = 'E460000000009'   



/*
delete FROM Transa01 WHERE  ESTADOFISCAL IS NOT NULL 

delete from cxcmovi1 WHERE ESTADOFISCAL IS NOT NULL

delete cxpmovi1 WHERE  ESTADOFISCAL IS NOT NULL 

delete from cajachica WHERE ESTADOFISCAL IS NOT NULL

delete cxcmovi2 WHERE  ESTADOFISCAL IS NOT NULL 
*/




delete transa01  where    estadofiscal is not null


Select * from transa01 where ncf= 'E340000004175      '  


update transa01 set grava=9900, nograva=0, ncf= 'E340000000188',estadofiscal=1,estadoimpresion=1 where ncf= 'E340000000187 '


ALTER SEQUENCE E34 RESTART WITH 4173
SELECT NEXT VALUE FOR E34