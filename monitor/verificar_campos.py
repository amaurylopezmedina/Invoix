"""
Script de verificación de campos para el endpoint estados-fiscales
Verifica que todos los campos requeridos para el link DGII estén presentes
"""

import json
import sys

# Campos requeridos según README del frontend
CAMPOS_REQUERIDOS = [
    'factura',
    'tipo_venta',
    'tipo_ecf',
    'encf',
    'estado_fiscal',
    'estado_fiscal_descripcion',
    'monto_facturado',
    'itbis_facturado',
    'monto_dgii',
    'itbis_dgii',
    'rncemisor',
    'resultado_estado_fiscal'
]

# Campos requeridos para link de verificación DGII
CAMPOS_LINK_DGII = [
    'rncemisor',
    'rnccomprador',
    'encf',
    'fecha_emision',      # formato DD-MM-YYYY
    'monto_facturado',
    'fecha_firma',        # formato DD-MM-YYYY HH:MM:SS
    'codigo_seguridad'
]

# Campos opcionales
CAMPOS_OPCIONALES = [
    'caja',
    'urlc',
    'dif_monto',
    'dif_itbis'
]

def verificar_respuesta(respuesta_json):
    """
    Verifica que la respuesta tenga todos los campos requeridos
    """
    print("=" * 60)
    print("VERIFICACIÓN DE CAMPOS - ENDPOINT ESTADOS-FISCALES")
    print("=" * 60)
    
    try:
        data = json.loads(respuesta_json)
    except json.JSONDecodeError as e:
        print(f"❌ ERROR: JSON inválido - {e}")
        return False
    
    # Verificar estructura principal
    if 'resultados' not in data:
        print("❌ ERROR: Falta el campo 'resultados' en la respuesta")
        return False
    
    if 'total_registros' not in data:
        print("❌ ADVERTENCIA: Falta el campo 'total_registros'")
    
    if 'totales' not in data:
        print("❌ ADVERTENCIA: Falta el campo 'totales'")
    
    if not data['resultados']:
        print("⚠️  ADVERTENCIA: No hay registros para verificar")
        return True
    
    # Verificar primer registro
    registro = data['resultados'][0]
    
    print("\n1. CAMPOS REQUERIDOS BÁSICOS:")
    print("-" * 60)
    todos_presentes = True
    for campo in CAMPOS_REQUERIDOS:
        if campo in registro:
            print(f"   ✅ {campo}: {registro[campo]}")
        else:
            print(f"   ❌ {campo}: FALTANTE")
            todos_presentes = False
    
    print("\n2. CAMPOS REQUERIDOS PARA LINK DGII:")
    print("-" * 60)
    link_completo = True
    for campo in CAMPOS_LINK_DGII:
        if campo in registro:
            valor = registro[campo]
            print(f"   ✅ {campo}: {valor}")
            
            # Validar formatos
            if campo == 'fecha_emision':
                if not validar_formato_fecha(valor, "DD-MM-YYYY"):
                    print(f"      ⚠️  Formato incorrecto, esperado DD-MM-YYYY")
            elif campo == 'fecha_firma':
                if not validar_formato_fecha_hora(valor, "DD-MM-YYYY HH:MM:SS"):
                    print(f"      ⚠️  Formato incorrecto, esperado DD-MM-YYYY HH:MM:SS")
        else:
            print(f"   ❌ {campo}: FALTANTE")
            link_completo = False
    
    print("\n3. CAMPOS OPCIONALES:")
    print("-" * 60)
    for campo in CAMPOS_OPCIONALES:
        if campo in registro:
            print(f"   ✅ {campo}: {registro[campo]}")
        else:
            print(f"   ⚠️  {campo}: No presente (opcional)")
    
    print("\n4. CAMPOS ADICIONALES:")
    print("-" * 60)
    todos_campos = set(CAMPOS_REQUERIDOS + CAMPOS_LINK_DGII + CAMPOS_OPCIONALES)
    campos_extra = set(registro.keys()) - todos_campos
    if campos_extra:
        for campo in campos_extra:
            print(f"   ℹ️  {campo}: {registro[campo]}")
    else:
        print("   (ninguno)")
    
    print("\n" + "=" * 60)
    print("RESUMEN:")
    print("=" * 60)
    print(f"✅ Campos básicos: {'COMPLETO' if todos_presentes else 'INCOMPLETO'}")
    print(f"✅ Campos link DGII: {'COMPLETO' if link_completo else 'INCOMPLETO'}")
    print(f"📊 Total de campos en respuesta: {len(registro)}")
    print("=" * 60)
    
    return todos_presentes and link_completo

def validar_formato_fecha(fecha, formato):
    """Valida que la fecha tenga el formato DD-MM-YYYY"""
    if not fecha or not isinstance(fecha, str):
        return False
    partes = fecha.split('-')
    if len(partes) != 3:
        return False
    dia, mes, anio = partes
    return len(dia) == 2 and len(mes) == 2 and len(anio) == 4

def validar_formato_fecha_hora(fecha_hora, formato):
    """Valida que la fecha tenga el formato DD-MM-YYYY HH:MM:SS"""
    if not fecha_hora or not isinstance(fecha_hora, str):
        return False
    partes = fecha_hora.split(' ')
    if len(partes) != 2:
        return False
    fecha, hora = partes
    
    # Validar fecha
    if not validar_formato_fecha(fecha, "DD-MM-YYYY"):
        return False
    
    # Validar hora
    partes_hora = hora.split(':')
    if len(partes_hora) != 3:
        return False
    hh, mm, ss = partes_hora
    return len(hh) == 2 and len(mm) == 2 and len(ss) == 2

if __name__ == "__main__":
    # Ejemplo de respuesta esperada
    ejemplo_respuesta = '''
    {
        "resultados": [
            {
                "factura": "FAC-001",
                "tipo_venta": "N/A",
                "tipo_ecf": "31",
                "encf": "E310000000004",
                "estado_fiscal": 5,
                "estado_fiscal_descripcion": "Aceptado por la DGII",
                "resultado_estado_fiscal": "1-Aceptado",
                "monto_facturado": 3681.60,
                "itbis_facturado": 561.60,
                "monto_dgii": 3681.60,
                "itbis_dgii": 0.00,
                "dif_monto": 0.00,
                "dif_itbis": 561.60,
                "rncemisor": "131695312",
                "rnccomprador": "132211464",
                "fecha_emision": "05-12-2025",
                "fecha_firma": "05-12-2025 15:40:29",
                "codigo_seguridad": "axAQfC",
                "urlc": "https://ecf.dgii.gov.do/...",
                "caja": "1"
            }
        ],
        "total_registros": 1,
        "totales": {
            "monto_facturado": 3681.60,
            "itbis_facturado": 561.60,
            "monto_dgii": 3681.60,
            "itbis_dgii": 0.00,
            "diferencia_monto": 0.00,
            "diferencia_itbis": 561.60
        }
    }
    '''
    
    print("\n🧪 VERIFICANDO EJEMPLO DE RESPUESTA...\n")
    verificar_respuesta(ejemplo_respuesta)
    
    print("\n\n💡 USO:")
    print("   Para verificar una respuesta real del servidor:")
    print("   python verificar_campos.py < respuesta.json")
    print("\n   O ejecutar:")
    print('   curl "http://localhost:8001/api/monitor/estados-fiscales?fecha_inicio=2025-12-01&fecha_fin=2025-12-10" | python verificar_campos.py')
