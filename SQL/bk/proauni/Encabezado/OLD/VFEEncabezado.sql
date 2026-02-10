create or alter view vFEEncabezado as
	--Facturas a credito y contado en pesos y dolares (Movimiento 03, 04, 33, 34) (comprobantes 31, 32, 44, 45, 46)
	--Incluye las devoluciones a contado (17) comprobante 34
	Select * from vFEEncabezadoTransa01


Union All

Select * from vFEEncabezadoCXCMovi1Directa

Union All

Select * from vFEEncabezadoCXCMovi1Devolucion

Union All

Select * from vFEEncabezadoCXCMovi1Debito

/*

Union All

	Select * from vFEEncabezadoCXPMovi1

UNION ALL
	--Gastos Menores (caja chica)
	Select * from vFEEncabezadoCajachica
	*/


