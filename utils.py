# utils.py
from bs4 import BeautifulSoup
import re
import unicodedata

def clean(text):
    """
    Limpia a fondo cualquier texto extraído del HTML, eliminando entidades HTML,
    espacios dobles, tabulaciones y saltos de línea.
    """
    if not text:
        return ""
    # Decodificar HTML si hubiera entidades codificadas
    soup_text = BeautifulSoup(str(text), "html.parser").get_text()
    # Eliminar espacios en blanco duplicados, saltos de línea y tabulaciones
    cleaned = " ".join(soup_text.split())
    return cleaned.strip()

def normalize_key(key_text):
    """
    Normaliza los títulos de SUNAT para convertirlos en claves de diccionario uniformes.
    Ejemplo: 'Fecha de Inscripción:' -> 'fecha_inscripcion'
    """
    text = clean(key_text).lower()
    # Quitar dos puntos al final
    if text.endswith(":"):
        text = text[:-1].strip()
    
    # Remover tildes y caracteres especiales
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    # Reemplazar espacios y caracteres no deseados por guiones bajos
    text = re.sub(r'[^a-z0-9_\s]', '', text)
    text = re.sub(r'\s+', '_', text)
    return text.strip("_")

def parse_key_value_pairs(soup):
    """
    Intenta extraer clave-valor utilizando selectores estándar de SUNAT.
    """
    data = {}
    # Selector principal
    items = soup.select(".list-group-item")
    for item in items:
        h = item.select_one(".list-group-item-heading")
        v = item.select_one(".list-group-item-text")
        if h and v:
            key = normalize_key(h.text)
            val = clean(v.text)
            if key:
                data[key] = val
    return data

def fallback_dom_search(soup, label_substrings):
    """
    Busca de manera flexible en el DOM un elemento que contenga alguna de las subcadenas (labels)
    y retorna el texto del elemento hermano o contenedor adyacente que represente su valor.
    Es altamente tolerante a cambios en los nombres de clases CSS de la SUNAT.
    """
    for text_node in soup.find_all(text=True):
        node_str = text_node.strip().lower()
        if any(sub in node_str for sub in label_substrings):
            parent = text_node.parent
            # Encontrar el valor adyacente. A menudo es el siguiente hermano en el DOM.
            # Buscaremos en los siguientes elementos hermanos del padre o del nodo mismo.
            # Caso 1: Siguiente elemento con texto
            sibling = parent.find_next_sibling()
            if sibling:
                val = clean(sibling.text)
                if val:
                    return val
            # Caso 2: Buscar en el siguiente texto disponible en el DOM
            next_el = parent.next_element
            for _ in range(10): # Limitar búsqueda secuencial para no degradar performance
                if not next_el:
                    break
                if hasattr(next_el, 'text') and next_el.text.strip() and next_el != parent:
                    val = clean(next_el.text)
                    # Evitar retornar otra etiqueta/título
                    if val and not any(sub in val.lower() for sub in label_substrings):
                        return val
                next_el = next_el.next_element
    return ""

def extract_razon_social_fallback(html):
    """
    Búsqueda directa por Regex para la Razón Social en el HTML de la SUNAT.
    Por lo general aparece como: 20100078901 - MI EMPRESA S.A.C.
    """
    # Expresión regular que busca 11 dígitos, opcionalmente guión o espacios, y luego el nombre limpio.
    match = re.search(r"(\d{11})\s*-\s*([^<>\-\n\r\t]+)", html)
    if match:
        name = clean(match.group(2))
        # Si contiene palabras de control de SUNAT, las quitamos
        if name and not any(x in name.lower() for x in ["número de ruc", "consulta"]):
            return name
    
    # Segundo fallback: Buscar en etiquetas <title> o encabezados h4
    match_title = re.search(r"<title>([^<]+)</title>", html, re.IGNORECASE)
    if match_title:
        title_text = clean(match_title.group(1))
        if "-" in title_text:
            parts = title_text.split("-")
            if len(parts) > 1 and parts[0].strip().isdigit():
                return clean("-".join(parts[1:]))
                
    return ""

def abbreviate_company_suffix(name):
    """
    Estandariza y unifica los sufijos de tipo societario de la Razón Social,
    removiendo puntos para mantener una estética limpia y consistente (ej: SRL, SAC, EIRL, SA).
    """
    if not name:
        return ""
    
    # 1. Reemplazar frases largas escritas por abreviaciones sin puntos
    replacements = [
        (r"\bSOCIEDAD COMERCIAL DE RESPONSABILIDAD LIMITADA\b", "SRL"),
        (r"\bEMPRESA INDIVIDUAL DE RESPONSABILIDAD LIMITADA\b", "EIRL"),
        (r"\bSOCIEDAD AN[OÓ]NIMA CERRADA\b", "SAC"),
        (r"\bSOCIEDAD AN[OÓ]NIMA ABIERTA\b", "SAA"),
        (r"\bSOCIEDAD AN[OÓ]NIMA\b", "SA"),
        (r"\bSOCIEDAD DE RESPONSABILIDAD LIMITADA\b", "SRL"),
        (r"\bSOCIEDAD CIVIL DE RESPONSABILIDAD LIMITADA\b", "S CIVIL RL"),
        (r"\bSOCIEDAD CIVIL\b", "S CIVIL")
    ]
    
    result = name
    for pattern, repl in replacements:
        result, count = re.subn(pattern, repl, result, flags=re.IGNORECASE)
        if count > 0:
            break  # Salir si se aplicó un reemplazo principal
            
    # 2. Estandarizar abreviaciones que ya venían con puntos desde SUNAT
    # Busca siglas con puntos al final o delimitadas y las convierte a siglas limpias
    abbrev_replacements = [
        (r"\bE\.I\.R\.L\.\b", "EIRL"),
        (r"\bS\.A\.C\.\b", "SAC"),
        (r"\bS\.R\.L\.\b", "SRL"),
        (r"\bS\.A\.A\.\b", "SAA"),
        (r"\bS\.A\.\b", "SA"),
    ]
    
    for pattern, repl in abbrev_replacements:
        result = re.sub(pattern, repl, result, flags=re.IGNORECASE)
            
    return " ".join(result.split())