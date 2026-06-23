# cache.py
import time
import logging
from config import REDIS_URL, CACHE_TTL

logger = logging.getLogger(__name__)

class BaseCache:
    def get(self, key):
        raise NotImplementedError()

    def set(self, key, value, ttl=None):
        raise NotImplementedError()

class MemoryCache(BaseCache):
    """
    Caché en memoria volátil (Python dict) con soporte de tiempo de expiración (TTL).
    Útil para desarrollo local, pruebas o servidores con una sola instancia.
    """
    def __init__(self):
        self._store = {}
        logger.info("Caché en memoria local (MemoryCache) inicializado.")

    def get(self, key):
        if key not in self._store:
            return None
        data, expires_at = self._store[key]
        if time.time() > expires_at:
            # Eliminar clave expirada
            del self._store[key]
            return None
        return data

    def set(self, key, value, ttl=None):
        ttl = ttl if ttl is not None else CACHE_TTL
        expires_at = time.time() + ttl
        self._store[key] = (value, expires_at)

class RedisCache(BaseCache):
    """
    Caché distribuido usando Redis, ideal para producción en SaaS.
    """
    def __init__(self, redis_url):
        import redis
        import json
        self.redis_client = redis.Redis.from_url(redis_url, socket_timeout=3.0, decode_responses=True)
        self.json = json
        # Probar conexión al inicio
        self.redis_client.ping()
        logger.info("Caché distribuido en Redis inicializado exitosamente.")

    def get(self, key):
        try:
            val = self.redis_client.get(key)
            if val:
                return self.json.loads(val)
        except Exception as e:
            logger.error(f"Error leyendo de Redis: {e}")
        return None

    def set(self, key, value, ttl=None):
        ttl = ttl if ttl is not None else CACHE_TTL
        try:
            val_str = self.json.dumps(value)
            self.redis_client.setex(key, ttl, val_str)
        except Exception as e:
            logger.error(f"Error escribiendo en Redis: {e}")

def get_cache_client():
    """
    Fábrica que retorna la mejor opción de caché disponible.
    Si REDIS_URL está configurado e instalado redis, usa RedisCache.
    De lo contrario, usa MemoryCache.
    """
    if REDIS_URL:
        try:
            import redis
            return RedisCache(REDIS_URL)
        except ImportError:
            logger.warning("Librería 'redis' no instalada. Usando MemoryCache como fallback.")
        except Exception as e:
            logger.warning(f"No se pudo conectar a Redis ({e}). Usando MemoryCache como fallback.")
    
    return MemoryCache()

# Instancia global del cliente de caché
cache = get_cache_client()
