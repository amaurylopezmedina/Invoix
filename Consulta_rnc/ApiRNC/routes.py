import functools
import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta

import jwt
import pyodbc
from api import logger, process_database_requests2
from database import get_db_connection
from flask import Blueprint, current_app, jsonify, request
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename

routes = Blueprint("routes", __name__)


@routes.route("/rnc_data", methods=["GET"])
@cross_origin()
def get_rnc_data():
    rnc = request.args.get("rnc", "")
    if not rnc:
        return jsonify({"message": "El parámetro RNC es obligatorio"}), 400

    # Ejecutar la función async de forma síncrona
    import asyncio

    return asyncio.run(process_database_requests2("RNCInfo"))
