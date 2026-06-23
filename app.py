# app.py
import time
import logging
from flask import Flask, jsonify, request

from sunat_service import (
    consultar_ruc,
    SunatNotFoundError,
    SunatBlockedError,
    SunatConnectionError,
    SunatParserError
)

# Configuración de Logging profesional para producción
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("flask_app")

app = Flask(__name__)

# ---------------------------------------------------------
# Soporte CORS nativo libre de dependencias externas
# ---------------------------------------------------------
@app.after_request
def enable_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    return response

# ---------------------------------------------------------
# Endpoint de monitoreo de salud (Health Check)
# ---------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "success": True,
        "status": "healthy",
        "timestamp": time.time()
    }), 200

# ---------------------------------------------------------
# Endpoint principal de consulta de RUC
# ---------------------------------------------------------
@app.route("/api/ruc/<ruc>", methods=["GET"])
def query_ruc(ruc):
    start_time = time.perf_counter()
    
    # Parámetro opcional para forzar la consulta en vivo y refrescar la caché
    bypass_cache = request.args.get("bypass_cache", "false").lower() == "true"
    
    try:
        # Consulta de RUC a través del servicio
        data, source = consultar_ruc(ruc, bypass_cache=bypass_cache)
        
        elapsed = round(time.perf_counter() - start_time, 4)
        logger.info(f"Consulta exitosa RUC {ruc} [{source}] en {elapsed}s")
        
        return jsonify({
            "success": True,
            "source": source,
            "elapsed_seconds": elapsed,
            "data": data
        }), 200

    except ValueError as e:
        # Validación de RUC (11 dígitos, caracteres correctos)
        elapsed = round(time.perf_counter() - start_time, 4)
        return jsonify({
            "success": False,
            "error": "Petición Incorrecta",
            "message": str(e),
            "elapsed_seconds": elapsed
        }), 400

    except SunatNotFoundError as e:
        # RUC no encontrado
        elapsed = round(time.perf_counter() - start_time, 4)
        return jsonify({
            "success": False,
            "error": "No Encontrado",
            "message": str(e),
            "elapsed_seconds": elapsed
        }), 404

    except SunatBlockedError as e:
        # Bloqueo temporal por parte de SUNAT (Captcha)
        elapsed = round(time.perf_counter() - start_time, 4)
        logger.warning(f"SUNAT bloqueó la petición para RUC {ruc} en {elapsed}s")
        return jsonify({
            "success": False,
            "error": "Límite Excedido / Captcha",
            "message": str(e),
            "elapsed_seconds": elapsed
        }), 429

    except SunatConnectionError as e:
        # Error al conectar con los servidores de SUNAT
        elapsed = round(time.perf_counter() - start_time, 4)
        logger.error(f"Fallo de conexión con SUNAT para RUC {ruc} en {elapsed}s. Detalle: {e}")
        return jsonify({
            "success": False,
            "error": "Servicio Temporalmente No Disponible",
            "message": "Los servidores de SUNAT no responden o están caídos. Inténtelo más tarde.",
            "elapsed_seconds": elapsed
        }), 503

    except SunatParserError as e:
        # Cambio drástico en la estructura del HTML
        elapsed = round(time.perf_counter() - start_time, 4)
        logger.critical(f"Error crítico de parseo para RUC {ruc} en {elapsed}s: {e}")
        return jsonify({
            "success": False,
            "error": "Error del Servidor",
            "message": "No se pudo analizar la información debido a cambios en la plataforma de origen.",
            "elapsed_seconds": elapsed
        }), 502

    except Exception as e:
        # Errores inesperados del servidor
        elapsed = round(time.perf_counter() - start_time, 4)
        logger.exception(f"Error inesperado procesando RUC {ruc} en {elapsed}s")
        return jsonify({
            "success": False,
            "error": "Error Interno del Servidor",
            "message": "Ocurrió un error inesperado al procesar su solicitud.",
            "elapsed_seconds": elapsed
        }), 500

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 5000))
    # Para producción, debug=False es obligatorio por seguridad
    app.run(host="0.0.0.0", port=port, debug=False)