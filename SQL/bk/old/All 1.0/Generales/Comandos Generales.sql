
--Alter table cxcmovi1 add MontoDGII numeric(18,2)


/*
update transa01 set estadofiscal=1, estadoimpresion=1 where estadofiscal=4 is not null --where  estadofiscal =1  
update cxPmovi1 set estadofiscal=100, estadoimpresion=1 /*where  estadofiscal  is not null --*/ where  ncf = 'B0100015173' --estadofiscal =1  
update cxcmovi1 set estadofiscal=4, estadoimpresion=1  WHERE TIPOMOVI ='02' AND FECHA = '20250226'    estadofiscal is not null --where  estadofiscal=4 
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



Select * from vfedetalle where  tipoecf = 34 and encf = 'E340000000018'





Select * from cxcmovi1 WHERE TIPOMOVI ='04' AND FECHA = '20250226'






--update transa01 set ncf= 'E320000003000',estadofiscal=1, estadoimpresion=1  where ncf = 'E320000001059'    

--update transa01 set ncf= 'E460000003000',estadofiscal=1, estadoimpresion=1  where ncf = 'E460000000009'   



/*
delete FROM Transa01 WHERE  ESTADOFISCAL IS NOT NULL 

delete from cxcmovi1 WHERE ESTADOFISCAL IS NOT NULL

delete cxpmovi1 WHERE  ESTADOFISCAL IS NOT NULL 

delete from cajachica WHERE ESTADOFISCAL IS NOT NULL

delete cxcmovi2 WHERE  ESTADOFISCAL IS NOT NULL 
*/








