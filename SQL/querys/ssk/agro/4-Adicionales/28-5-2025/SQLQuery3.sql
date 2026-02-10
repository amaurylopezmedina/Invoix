Select * from transa01 where numero = 'A00000209311'

Select * from vfeencabezado where numerofacturainterna = 'A00000209311'

Select * from tradetalle where numero = 'A00000209311'

update transa01 set estadofiscal= 1, estadoimpresion=1 where ncf in ('E310000000073')

Select * from empresa