# 🚀 API RUC SUNAT - SaaS Ready (Fines de Prueba)

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.x-black.svg?style=for-the-badge&logo=flask&logoColor=white)
![Render](https://img.shields.io/badge/Render-Hosted-46E3B7.svg?style=for-the-badge&logo=render&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-Cache-DC382D.svg?style=for-the-badge&logo=redis&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)

¡Qué tal gente! Habla **Jhoyner Correa Hinostroza**. Les presento esta API profesional que armé para consultar datos completos de cualquier RUC directamente desde los servidores de la **SUNAT (Perú)** sin usar navegadores pesados ni lentos.

> [!WARNING]
> **Aviso Importante:** Esta API ha sido desarrollada con fines de prueba y demostración. Estaré subiendo actualizaciones constantemente para mejorar su rendimiento, robustez y añadir nuevas funciones. 😉

Desarrollada por este papi: **Jhoyner Correa** 😎.

---

## 🛠️ ¿Cómo funciona esta joya por dentro?

El gran problema del scraping tradicional (como Selenium o Playwright) es que consume demasiada memoria RAM, es lento y los hostings te cobran un ojo de la cara. 

Esta API la diseñé usando solo **peticiones HTTP optimizadas** con `requests` y `BeautifulSoup`. Para evitar que la SUNAT nos bloquee la IP o nos pida CAPTCHA, la API hace lo siguiente:
1. **Simulación Humana:** Hace una petición `GET` rápida al portal de SUNAT para establecer la sesión y capturar las cookies reales (`JSESSIONID`).
2. **Rotación de Identidad:** En cada consulta rotamos una lista de **User-Agents reales** de navegadores modernos (Chrome, Firefox, Safari).
3. **Lectura Inteligente (DOM Traversal):** Si la SUNAT cambia sus estilos o nombres de clase de HTML, la API no se rompe. Busca directamente las palabras clave en los textos del HTML ("estado", "condición", "inscripción") y extrae el valor que tiene al lado. Y como último plan de respaldo, usa **expresiones regulares (Regex)**.
4. **Capa de Caché Adaptable:** Si tienes Redis configurado, guardará ahí los resultados. Si no, usará la memoria RAM de tu servidor local. Así, si consultas el mismo RUC dos veces, la segunda respuesta toma menos de **5 milisegundos**.

---

## ⚙️ Estructura del Código

* `app.py`: El corazón del servidor Flask. Gestiona las rutas, habilita CORS de forma nativa (para consumir la API desde cualquier frontend) y procesa los códigos de error HTTP adecuados.
* `sunat_service.py`: Aquí está la magia del scraping, control de sesiones, reintentos y la extracción segura de los representantes legales y locales anexos.
* `utils.py`: Herramientas de limpieza estricta de HTML y normalización de llaves a formato `snake_case`.
* `cache.py`: Configura de manera automática la memoria local o la base de datos de Redis.
* `config.py`: Centraliza los parámetros como timeouts, reintentos y encabezados HTTP.

---

## 🚀 Instalación Rápida para Pruebas

Si quieres probarla en tu propia máquina, sigue estos comandos:

### 1. Clonar el repositorio
```bash
git clone https://github.com/Jhoyner-Correa/api-ruc-sunat-saas.git
cd api-ruc-sunat-saas
```

### 2. Crear y activar tu entorno virtual (Recomendado)
```bash
# En Windows (PowerShell/CMD):
python -m venv venv
.\venv\Scripts\activate

# En macOS/Linux:
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar librerías
```bash
pip install -r requirements.txt
```

### 4. Ejecutar el test en consola
```bash
python test_api.py
```
*Este test hará consultas reales a la SUNAT e imprimirá los JSON formateados en tu terminal.*

### 5. Correr la API localmente
```bash
python app.py
```
*Ya podrás hacer peticiones en tu navegador o Postman en `http://127.0.0.1:5000/api/ruc/<RUC_A_CONSULTAR>`.*

---

## 📡 Endpoints de Prueba Públicos (Desplegado en Render)

Tengo un demo desplegado y funcionando en vivo en Render. Puedes probarlo directamente desde aquí:

### 🩺 1. Estado de la API (Health Check)
* **URL:** [https://api-ruc-sunat-saas.onrender.com/health](https://api-ruc-sunat-saas.onrender.com/health)
* **Respuesta esperada:**
```json
{
  "status": "healthy",
  "success": true,
  "timestamp": 1782192069.002
}
```

### 🔍 2. Consultar Datos de RUC
* **URL:** [https://api-ruc-sunat-saas.onrender.com/api/ruc/20131312955](https://api-ruc-sunat-saas.onrender.com/api/ruc/20131312955) *(RUC de la SUNAT)*
* **Respuesta JSON:**
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
*Tip: Si refrescas la consulta, notarás que responde de inmediato (en milisegundos) porque el sistema lee la caché en lugar de ir otra vez a la SUNAT.*

---

## 🌎 Despliegue en tu propio Hosting

Si quieres subir tu propia versión de esta API a Render o Railway:
1. Crea un **Web Service** conectado a tu copia de este repositorio.
2. Usa el comando de construcción: `pip install -r requirements.txt`.
3. Para el comando de inicio en producción, usa **Gunicorn** (incluido en las dependencias) para soportar múltiples peticiones en paralelo:
   ```bash
   gunicorn --workers 3 --bind 0.0.0.0:$PORT app:app
   ```
4. (Opcional) Si creas una base de datos Redis, agrega la variable de entorno `REDIS_URL` en tu panel de control para activar el caché distribuido.

---

## 📈 Próximas Actualizaciones
* Integración con proxies rotativos para evitar bloqueos dinámicos en consultas masivas.
* Búsqueda por Razón Social (para consultar RUCs sabiendo solo el nombre de la empresa).
* Optimización de consultas paralelas en sub-peticiones.
