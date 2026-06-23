# config.py
import os

# Configuración del servidor Flask
PORT = int(os.getenv("PORT", 5000))
DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

# Configuración de conexiones HTTP (SUNAT)
TIMEOUT = int(os.getenv("SUNAT_TIMEOUT", 8)) # Timeout de conexión y lectura
MAX_RETRIES = int(os.getenv("SUNAT_MAX_RETRIES", 2)) # Máximo de reintentos
BACKOFF_FACTOR = float(os.getenv("SUNAT_BACKOFF_FACTOR", 0.5))

# Configuración de Caché
REDIS_URL = os.getenv("REDIS_URL", "") # Ejemplo: redis://:password@localhost:6379/0
CACHE_TTL = int(os.getenv("CACHE_TTL", 86400)) # 24 horas por defecto (en segundos)

# Encabezados base para simular navegador real
DEFAULT_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Origin": "https://e-consultaruc.sunat.gob.pe",
    "Referer": "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1"
}

# Rotación de User-Agents para evitar bloqueos
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
]
