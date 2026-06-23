# 🚀 API RUC SUNAT - SaaS Production Ready

Una API profesional, modular y de alto rendimiento desarrollada en **Python (Flask)** para consultar datos completos de RUC directamente desde los servidores de la **SUNAT (Perú)**. 

Este proyecto está diseñado para funcionar en entornos de producción (SaaS), operando **sin navegadores pesados** (sin Selenium, sin Playwright) mediante peticiones HTTP optimizadas con `requests` y `BeautifulSoup`, logrando latencias mínimas y alta tolerancia a fallos.

---

## ✨ Características Principales

* ⚡ **Sin Navegador (Headless HTTP):** Consultas directas al servidor de SUNAT mediante POSTs optimizados para máxima velocidad.
* 🛡️ **Tolerancia Extrema a Cambios de HTML:** Si SUNAT cambia sus clases CSS de diseño, la API utiliza un algoritmo de búsqueda recursiva en el DOM basado en texto semántico y expresiones regulares (Regex) de respaldo.
* 📦 **Capa de Caché Inteligente (Redis & RAM):** Sistema de caché auto-configurable. Usa **Redis** para entornos distribuidos (SaaS) y conmuta automáticamente a **MemoryCache** en RAM local para desarrollo. Las consultas recurrentes tardan menos de **5ms**.
* 🔄 **Evasión Activa de Bloqueos:** Rotación automática de User-Agents y simulación estricta de cookies humanas para evitar baneos de IP o solicitudes de CAPTCHA.
* 🔍 **Consultas Detalladas Completas:**
  * Razón Social (100% desinfectada de HTML).
  * Tipo de Contribuyente, Estado y Condición.
  * Dirección/Domicilio Fiscal.
  * Fechas de Inscripción y de Inicio de Actividades.
  * Sistema de Emisión y Sistema de Contabilidad.
  * Actividades Económicas (lista sanitizada).
  * **Representantes Legales** (lista estructurada).
  * **Locales Anexos** (lista estructurada).
* 🩺 **SaaS Ready:**
  * Endpoint `/health` integrado para monitoreo automático en la nube.
  * Telemetría de tiempos de ejecución (`elapsed_seconds`) en cada respuesta JSON.
  * Soporte de CORS nativo (sin librerías extras) para consumo desde cualquier frontend (React, Angular, Vue, Flutter, etc.).
  * Mapeo semántico de códigos de error HTTP (`400`, `404`, `429`, `503`, `502`).

---

## 🛠️ Arquitectura del Código

La solución está separada en módulos independientes para facilitar el mantenimiento y escalabilidad:

* `app.py`: Servidor Flask, CORS, health checks y enrutamiento con manejo global de errores.
* `sunat_service.py`: Lógica central del scraper, control de cookies, reintentos con retraso exponencial y subconsultas aisladas.
* `utils.py`: Normalizadores de texto, desinfectantes HTML y algoritmos de fallbacks en DOM/Regex.
* `cache.py`: Interfaz de caché unificada para Redis y memoria local con soporte TTL (Time-to-Live).
* `config.py`: Parámetros globales (timeouts, reintentos, user-agents y variables de entorno).

---

## 🚀 Instalación y Uso Local

### 1. Clonar el repositorio
```bash
git clone https://github.com/Jhoyner-Correa/api-ruc-sunat-saas.git
cd api-ruc-sunat-saas
```

### 2. Configurar entorno virtual (Recomendado)
```bash
# En Windows:
python -m venv venv
.\venv\Scripts\activate

# En macOS/Linux:
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Probar en consola (Prueba rápida)
```bash
python test_api.py
```
*Este script simula consultas para un RUC válido de SUNAT, un RUC inexistente y valida formatos erróneos.*

### 5. Iniciar el servidor de desarrollo
```bash
python app.py
```
*El servidor se ejecutará localmente en `http://127.0.0.1:5000`.*

---

## 📡 Endpoints de la API

### 1. Health Check
* **Método:** `GET`
* **Ruta:** `/health`
* **Descripción:** Comprueba si el servidor está en línea. Usado por plataformas cloud (Render, AWS, etc.) para validar el estado del contenedor.
* **Respuesta (`200 OK`):**
```json
{
  "status": "healthy",
  "success": true,
  "timestamp": 1782192069.002
}
```

### 2. Consultar RUC
* **Método:** `GET`
* **Ruta:** `/api/ruc/<ruc>`
* **Parámetros Opcionales:** `bypass_cache=true` (ignora el caché y consulta en vivo directamente a SUNAT).
* **Respuesta Exitosa (`200 OK`):**
```json
{
  "success": true,
  "source": "live",
  "elapsed_seconds": 1.245,
  "data": {
    "ruc": "20131312955",
    "razonSocial": "SUPERINTENDENCIA NACIONAL DE ADUANAS Y DE ADMINISTRACION TRIBUTARIA",
    "tipoContribuyente": "INSTITUCIONES PUBLICAS",
    "estado": "ACTIVO",
    "condicion": "HABIDO",
    "direccionFiscal": "AV. GARCILASO DE LA VEGA NRO. 1472 LIMA - LIMA - LIMA",
    "fechaInscripcion": "04/05/1993",
    "fechaInicioActividades": "09/06/1988",
    "actividadesEconomicas": [],
    "sistemaEmision": "MANUAL/COMPUTARIZADO",
    "sistemaContabilidad": "COMPUTARIZADO",
    "representantesLegales": [
      {
        "tipoDocumento": "DNI",
        "documento": "02808305",
        "nombre": "RAMIREZ GARCIA CARLOS MARCELINO",
        "cargo": "GERENTE DE FINANZAS",
        "fechaDesde": "25/07/2025"
      }
    ],
    "anexos": [
      {
        "codigo": "0195",
        "tipo": "AG. AGENCIA",
        "direccion": "CAL.PROLONGACION TACNA LOTE. 150 LA LIBERTAD - ASCOPE - RAZURI",
        "actividad": "-"
      }
    ]
  }
}
```

---

## 🌍 Configuración de Producción (Despliegue en la Nube)

Este proyecto está listo para ser desplegado en servicios como **Render**, **Railway**, **Heroku** o en servidores dedicados (**DigitalOcean VPS**).

### Variables de Entorno soportadas:
* `REDIS_URL`: URL de conexión a tu base de datos Redis (ej: `redis://:contraseña@host:puerto/0`). Si no se configura, usará automáticamente **Memory Cache** en RAM.
* `CACHE_TTL`: Tiempo de persistencia de la caché del RUC (por defecto `86400` segundos = 24 horas).
* `SUNAT_TIMEOUT`: Tiempo límite de espera para respuestas de la SUNAT (por defecto `8` segundos).
* `PORT`: Puerto de escucha del servidor (asignado automáticamente por la mayoría de hostings).

### Comando de Arranque en Producción:
No inicies el servidor usando `python app.py` en producción. Utiliza **Gunicorn** (incluido en `requirements.txt`) para manejar concurrencia:
```bash
gunicorn --workers 3 --bind 0.0.0.0:$PORT app:app
```

---

## 📄 Licencia
Este proyecto es de código abierto y está disponible bajo la licencia MIT.
