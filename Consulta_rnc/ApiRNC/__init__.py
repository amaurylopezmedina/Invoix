from flask import Flask

app = Flask(__name__)

# Importar las rutas después de crear la aplicación para evitar ciclos de importación
import routes
