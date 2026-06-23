# sunat_service.py
import logging
import random
import re
import requests
from bs4 import BeautifulSoup
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

import config
from cache import cache
from utils import clean, normalize_key, parse_key_value_pairs, fallback_dom_search, extract_razon_social_fallback

# Configuración de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

URL = "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias"

# ---------------------------------------------------------
# Excepciones personalizadas para control fino en la API
# ---------------------------------------------------------
class SunatError(Exception):
    """Clase base para todos los errores relacionados con SUNAT."""
    pass

class SunatConnectionError(SunatError):
    """Excepción cuando SUNAT está caído o el tiempo de espera se agota."""
    pass

class SunatBlockedError(SunatError):
    """Excepción cuando SUNAT detecta comportamiento inusual o pide CAPTCHA."""
    pass

class SunatNotFoundError(SunatError):
    """Excepción cuando el RUC consultado no existe."""
    pass

class SunatParserError(SunatError):
    """Excepción cuando el HTML cambia drásticamente y no es posible parsearlo."""
    pass

# ---------------------------------------------------------
# Inicialización de Sesión HTTP con optimizaciones SaaS
# ---------------------------------------------------------
def get_session():
    """
    Crea una sesión de requests con User-Agent aleatorio y
    estrategia de reintentos exponencial para tolerar microcaídas de red.
    """
    session = requests.Session()
    
    # Rotación de User-Agent
    ua = random.choice(config.USER_AGENTS)
    headers = config.DEFAULT_HEADERS.copy()
    headers["User-Agent"] = ua
    session.headers.update(headers)
    
    # Configurar reintentos
    retries = Retry(
        total=config.MAX_RETRIES,
        backoff_factor=config.BACKOFF_FACTOR,
        status_forcelist=[500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def get_field_flexible(data, candidates):
    """
    Busca de manera flexible en el diccionario de datos.
    Primero busca coincidencia exacta, luego coincidencia parcial (substring).
    """
    # 1. Búsqueda exacta
    for candidate in candidates:
        if candidate in data:
            return data[candidate]
            
    # 2. Búsqueda parcial (clave dentro de candidato o candidato dentro de clave)
    for k, v in data.items():
        for candidate in candidates:
            if candidate in k or k in candidate:
                return v
    return ""

# ---------------------------------------------------------
# Consultas secundarias (Representantes y Locales Anexos)
# ---------------------------------------------------------
def get_representantes(session, ruc):
    """
    Obtiene la lista estructurada de representantes legales.
    Si falla, retorna una lista vacía para no arruinar la consulta principal.
    """
    payload = {
        "accion": "getRepLeg",
        "contexto": "ti-it",
        "modo": "1",
        "nroRuc": ruc,
        "desRuc": ""
    }
    try:
        r = session.post(URL, data=payload, timeout=config.TIMEOUT)
        if r.status_code != 200:
            return []
            
        soup = BeautifulSoup(r.text, "html.parser")
        reps = []
        
        # Intentar con tbody tr, y si falla buscar todas las filas
        rows = soup.select("tbody tr")
        if not rows:
            rows = soup.find_all("tr")
            
        for row in rows:
            cols = [clean(c.text) for c in row.find_all(["td", "th"])]
            if len(cols) < 5:
                continue
            # Evitar cabeceras
            if any(h in cols[1].lower() for h in ["documento", "nro", "numero"]):
                continue
                
            reps.append({
                "tipoDocumento": cols[0],
                "documento": cols[1],
                "nombre": cols[2],
                "cargo": cols[3],
                "fechaDesde": cols[4]
            })
        return reps
    except Exception as e:
        logger.warning(f"Error parseando representantes para RUC {ruc}: {e}")
        return []

def get_anexos(session, ruc):
    """
    Obtiene la lista estructurada de locales anexos.
    Si falla, retorna una lista vacía para no arruinar la consulta principal.
    """
    payload = {
        "accion": "getLocAnex",
        "contexto": "ti-it",
        "modo": "1",
        "nroRuc": ruc,
        "desRuc": ""
    }
    try:
        r = session.post(URL, data=payload, timeout=config.TIMEOUT)
        if r.status_code != 200:
            return []
            
        soup = BeautifulSoup(r.text, "html.parser")
        anexos = []
        
        rows = soup.select("tbody tr")
        if not rows:
            rows = soup.find_all("tr")
            
        for row in rows:
            cols = [clean(c.text) for c in row.find_all(["td", "th"])]
            if len(cols) < 4:
                continue
            # Evitar cabeceras
            if any(h in cols[0].lower() for h in ["codigo", "código"]):
                continue
                
            anexos.append({
                "codigo": cols[0],
                "tipo": cols[1],
                "direccion": cols[2],
                "actividad": cols[3]
            })
        return anexos
    except Exception as e:
        logger.warning(f"Error parseando locales anexos para RUC {ruc}: {e}")
        return []

# ---------------------------------------------------------
# Consulta Principal RUC
# ---------------------------------------------------------
def consultar_ruc(ruc, bypass_cache=False):
    """
    Consulta los datos completos del RUC desde la SUNAT.
    Implementa caché integrada, reintentos y tolerancia extrema a cambios HTML.
    """
    # 1. Validación básica de formato
    if not ruc.isdigit() or len(ruc) != 11:
        raise ValueError("El RUC debe consistir exactamente de 11 dígitos numéricos.")
        
    cache_key = f"ruc:{ruc}"
    
    # 2. Intentar leer de la caché si no se solicita omitirla
    if not bypass_cache:
        try:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"RUC {ruc} recuperado desde la caché.")
                return cached_data, "cache"
        except Exception as e:
            logger.warning(f"Fallo al leer de la caché: {e}")

    # 3. Inicializar sesión e intentar establecer cookies
    session = get_session()
    
    # Hacer una petición GET ligera inicial para simular comportamiento humano y obtener sesión/cookies
    try:
        session.get("https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp", timeout=config.TIMEOUT)
    except Exception as e:
        logger.warning(f"Petición GET inicial falló, se intentará POST directamente. Detalle: {e}")

    # 4. Enviar consulta RUC por POST
    payload = {
        "accion": "consPorRuc",
        "nroRuc": ruc,
        "contexto": "ti-it",
        "modo": "1",
        "rbtnTipo": "1",
        "token": "123"
    }
    
    try:
        r = session.post(URL, data=payload, timeout=config.TIMEOUT)
    except requests.exceptions.RequestException as e:
        raise SunatConnectionError(f"No se pudo conectar a la SUNAT: {e}")

    if r.status_code != 200:
        raise SunatConnectionError(f"SUNAT respondió con código de estado HTTP {r.status_code}")

    html = r.text

    # 5. Detección de bloqueos y CAPTCHA
    html_lower = html.lower()
    if "captcha" in html_lower or "bloque" in html_lower or "solicita el codigo" in html_lower:
        raise SunatBlockedError("La consulta fue bloqueada por SUNAT (se solicita CAPTCHA / IP restringida).")

    # 6. Detección de RUC no existente
    # SUNAT suele reportar que no existe, no es válido o no está registrado.
    if any(msg in html_lower for msg in ["no existe", "no registrado", "no es valido", "no es válido", "no es correcto"]):
        raise SunatNotFoundError(f"El RUC {ruc} no existe o no está registrado en SUNAT.")

    # 7. Parseo del HTML
    soup = BeautifulSoup(html, "html.parser")
    
    # Intento 1: Parseo estructurado básico
    data = parse_key_value_pairs(soup)
    
    # Recuperación flexible de campos
    tipo_contribuyente = get_field_flexible(data, ["tipo_contribuyente", "tipo_de_contribuyente"])
    estado = get_field_flexible(data, ["estado", "estado_del_contribuyente", "estado_contribuyente"])
    condicion = get_field_flexible(data, ["condicion", "condicion_del_contribuyente", "condicion_contribuyente"])
    direccion = get_field_flexible(data, ["domicilio_fiscal", "direccion", "direccion_fiscal"])
    fecha_inscripcion = get_field_flexible(data, ["fecha_de_inscripcion", "fecha_inscripcion"])
    fecha_inicio_actividades = get_field_flexible(data, ["fecha_de_inicio_de_actividades", "fecha_inicio_actividades", "inicio_de_actividades"])
    sistema_emision = get_field_flexible(data, ["sistema_emision_de_comprobante", "sistema_emision", "sistema_de_emision"])
    sistema_contabilidad = get_field_flexible(data, ["sistema_contabilidad", "sistema_de_contabilidad"])
    actividad_text = get_field_flexible(data, ["actividad_economica", "actividades_economicas", "actividad_es_economica_s"])

    # Fallback 1: Extraer Razón Social usando varias estrategias
    razon_social = ""
    # Estrategia A: Del campo "número de ruc" parseado (ej: "20100078901 - MI EMPRESA SAC")
    ruc_val = get_field_flexible(data, ["numero_de_ruc", "numero_ruc", "ruc"])
    if ruc_val and "-" in ruc_val:
        parts = ruc_val.split("-")
        if len(parts) > 1:
            razon_social = clean("-".join(parts[1:]))

    # Estrategia B: Regex directa en el HTML
    if not razon_social:
        razon_social = extract_razon_social_fallback(html)

    # Estrategia C: DOM traversal buscando palabras clave
    if not razon_social:
        val_dom = fallback_dom_search(soup, ["número de ruc", "numero de ruc", "ruc"])
        if val_dom and "-" in val_dom:
            parts = val_dom.split("-")
            if len(parts) > 1:
                razon_social = clean("-".join(parts[1:]))

    # Fallback 2: Si el parseo asociativo falló por completo debido a cambio de clases, aplicar DOM Traversal flexible
    if not tipo_contribuyente:
        tipo_contribuyente = fallback_dom_search(soup, ["tipo contribuyente", "tipo de contribuyente"])
    if not estado:
        estado = fallback_dom_search(soup, ["estado del contribuyente", "estado de contribuyente", "estado"])
    if not condicion:
        condicion = fallback_dom_search(soup, ["condición del contribuyente", "condicion del contribuyente", "condicion"])
    if not direccion:
        direccion = fallback_dom_search(soup, ["domicilio fiscal", "direccion fiscal", "domicilio"])
    if not fecha_inscripcion:
        fecha_inscripcion = fallback_dom_search(soup, ["fecha de inscripción", "fecha de inscripcion", "fecha inscripcion"])
    if not fecha_inicio_actividades:
        fecha_inicio_actividades = fallback_dom_search(soup, ["fecha de inicio de actividades", "fecha inicio de actividades", "inicio de actividades"])
    if not sistema_emision:
        sistema_emision = fallback_dom_search(soup, ["sistema de emisión", "sistema de emision", "sistema emision"])
    if not sistema_contabilidad:
        sistema_contabilidad = fallback_dom_search(soup, ["sistema de contabilidad", "sistema contabilidad"])
    if not actividad_text:
        actividad_text = fallback_dom_search(soup, ["actividad económica", "actividad economica", "actividades economicas"])

    # 8. Limpieza de Actividad Económica (devolver una lista limpia)
    actividades = []
    if actividad_text:
        # SUNAT separa las actividades por comas, puntos o saltos de línea
        actividades = [clean(act) for act in re.split(r'[,;\n]', actividad_text) if clean(act)]

    # 9. Control de consistencia crítico: Razón Social es obligatoria
    if not razon_social and not tipo_contribuyente:
        raise SunatParserError("No se pudieron parsear los datos. SUNAT cambió drásticamente su estructura HTML.")

    # 10. Consultar Representantes y Anexos usando la misma sesión activa
    representantes = get_representantes(session, ruc)
    anexos = get_anexos(session, ruc)

    # 11. Estructura de salida final uniforme
    result = {
        "ruc": ruc,
        "razonSocial": razon_social,
        "tipoContribuyente": tipo_contribuyente,
        "estado": estado,
        "condicion": condicion,
        "direccionFiscal": direccion,
        "fechaInscripcion": fecha_inscripcion,
        "fechaInicioActividades": fecha_inicio_actividades,
        "actividadesEconomicas": actividades,
        "sistemaEmision": sistema_emision,
        "sistemaContabilidad": sistema_contabilidad,
        "representantesLegales": representantes,
        "anexos": anexos
    }

    # 12. Guardar el resultado en caché para futuras llamadas rápidas
    try:
        cache.set(cache_key, result)
    except Exception as e:
        logger.warning(f"No se pudo escribir en la caché para RUC {ruc}: {e}")

    return result, "live"