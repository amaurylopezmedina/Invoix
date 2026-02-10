import requests
import json

# URL del servicio (ajusta según sea necesario)
url = 'http://localhost:5000/procesar'

# Datos de prueba
datos = {
    'RNCEmisor': '130239061',
    'eNCF': 'E320000001074'
}

# Realizar la petición POST
response = requests.post(
    url,
    data=json.dumps(datos),
    headers={'Content-Type': 'application/json'}
)

# Imprimir la respuesta
print('Código de estado:', response.status_code)
print('Respuesta:')
print(json.dumps(response.json(), indent=4))