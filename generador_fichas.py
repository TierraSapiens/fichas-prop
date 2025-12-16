# ------------------------------------------------------------
# generador_fichas.py V 1.3.txt —VERSION CORREGIDA Sin Selenium ¿?Playwright
# ------------------------------------------------------------

import os
import json
import random
import string
import re
import urllib.parse
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from scrapers.scrapear_zonaprop import scrapear_zonaprop
import logging
logger = logging.getLogger(__name__)

def detectar_scraper(url):
    url = url.lower()

    if "zonaprop.com.ar" in url:
        return "zonaprop"

    # futuros:
    # if "argenprop.com" in url:
    #     return "argenprop"

    return None

# -------------------
# 1. Generar ID único
# -------------------
def generar_id_unico():
    caracteres = string.ascii_letters + string.digits
    largo = 20

    if os.path.exists("ids_generados.json"):
        with open("ids_generados.json", "r", encoding="utf-8") as f:
            usados = set(json.load(f))
    else:
        usados = set()

    while True:
        nuevo_id = ''.join(random.choice(caracteres) for _ in range(largo))
        if nuevo_id not in usados:
            usados.add(nuevo_id)
            break

    with open("ids_generados.json", "w", encoding="utf-8") as f:
        json.dump(list(usados), f, indent=2)

    return nuevo_id

# --------------------------------------------------------
# 2. Extraer datos OpenGraph (Título, Descripción, Imagen)
# --------------------------------------------------------
def extraer_datos_opengraph(url):
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
    except Exception:
        return "", "", "", None

    def og(prop):
        tag = soup.find("meta", property=f"og:{prop}")
        return tag.get("content").strip() if tag and tag.get("content") else None

    titulo = og("title") or ""
    descripcion = og("description") or ""

    imagen = og("image")

# -------------------------------------------
#Intentar detectar "Un Precio" desde título o descripción...
# -------------------------------------------
    precio = "Consultar"
    posibles = [titulo, descripcion]
    patrones = [
        r"USD\s?[0-9\.,]+",
        r"U\$S\s?[0-9\.,]+",
        r"\$\s?[0-9\.,]+"
    ]

    for texto in posibles:
        if not texto:
            continue
        for p in patrones:
            m = re.search(p, texto, flags=re.IGNORECASE)
            if m:
                precio = m.group(0)
                break
        if precio != "Consultar":
            break

    return titulo, descripcion, precio, imagen

# ---------------------------------------------
# 3. "Descargar imagen" (Hasta ahora 0 exito.!!)
# ---------------------------------------------
def _extraer_url_imagen(soup):
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        return og.get("content").strip()
    link_img = soup.find("link", rel="image_src")
    if link_img and link_img.get("href"):
        return link_img.get("href").strip()
    img = soup.find("img")
    if img:
        for attr in ("src", "data-src", "data-lazy-src"):
            u = img.get(attr)
            if u:
                return u
        srcset = img.get("srcset")
        if srcset:
            first = srcset.split(",")[0].strip().split(" ")[0]
            return first
    return None


def descargar_imagen(url_img, carpeta_ficha, pagina_base=None, timeout=8):
    """
    Intenta descargar una imagen. Si url_img es relativa, la resuelve con pagina_base.
    Devuelve el nombre del archivo (ej: 'foto.jpg') o None.
    """
    try:
        if not url_img:
            return None
        if pagina_base and not urllib.parse.urlparse(url_img).netloc:
            url_img = urllib.parse.urljoin(pagina_base, url_img)
        for intento in range(2):
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                r = requests.get(url_img, headers=headers, timeout=timeout)
                r.raise_for_status()
                ext = os.path.splitext(urllib.parse.urlparse(url_img).path)[1].lower()
                os.makedirs(carpeta_ficha, exist_ok=True)
                if ext not in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
                    ext = ".jpg"
                nombre = "foto" + ext
                ruta = os.path.join(carpeta_ficha, nombre)
                with open(ruta, "wb") as f:
                    f.write(r.content)
                return nombre
            except Exception:
                time.sleep(0.5)
                continue
    except Exception:
        pass
    return None

# -------------------------------------------
# 4. Crear ficha
# -------------------------------------------
def crear_ficha(url_propiedad, telegram_url, agencia):
    logger.info("ENTRO A crear_ficha | url=%s", url_propiedad)

    # 1. Preparar carpetas
    ficha_id = generar_id_unico()
    carpeta = os.path.join("fichas", ficha_id)
    os.makedirs(carpeta, exist_ok=True)

    logger.info(
        "--- Generando Ficha ID: %s | agencia=%s ---",
        ficha_id,
        agencia
    )

    # Inicializamos variables por defecto
    titulo = "Sin título"
    descripcion = "Sin descripción"
    precio = "Consultar"
    ubicacion = "Ubicación no especificada"
    detalles = "Información adicional no disponible."
    imagenes_candidatas = []

    # 2. ELEGIR SCRAPER
    tipo_scraper = detectar_scraper(url_propiedad)
    logger.info("Scraper detectado: %s", tipo_scraper)

    if tipo_scraper == "zonaprop":
        logger.info("Usando scraper Zonaprop (Playwright)")
        try:
            datos = scrapear_zonaprop(url_propiedad)

            titulo = datos.get("titulo", "")
            precio = datos.get("precio", "Consultar")
            ubicacion = datos.get("ubicacion", "")
            descripcion = datos.get("descripcion", "")
            imagenes_candidatas = datos.get("imagenes", [])

            caracteristicas = datos.get("caracteristicas", {})
            if caracteristicas:
                detalles = " | ".join(
                    f"{k}: {v}" for k, v in caracteristicas.items()
                )

        except Exception:
            logger.exception(
                "ERROR usando Playwright para Zonaprop, fallback a OpenGraph"
            )
            tipo_scraper = None

    # 3. FALLBACK
    if tipo_scraper != "zonaprop":
        logger.info("Usando método OpenGraph (fallback)")
        t_og, d_og, p_og, img_og = extraer_datos_opengraph(url_propiedad)
        if t_og: titulo = t_og
        if d_og: descripcion = d_og
        if p_og != "Consultar": precio = p_og
        if img_og: imagenes_candidatas.append(img_og)

    # 4. PROCESAR IMAGEN
    nombre_img_final = None
    for img_url in imagenes_candidatas:
        logger.info("Intentando descargar imagen: %s", img_url)
        nombre = descargar_imagen(img_url, carpeta, pagina_base=url_propiedad)
        if nombre:
            nombre_img_final = nombre
            break

    if nombre_img_final:
        imagen_publica = (
            f"https://tierrasapiens.github.io/fichas-prop/"
            f"fichas/{ficha_id}/{nombre_img_final}"
        )
    else:
        logger.warning("No se pudo descargar imagen, usando default")
        imagen_publica = "https://tierrasapiens.github.io/fichas-prop/default.jpg"

    # 5. GENERAR HTML
    try:
        with open("ficha_template.html", "r", encoding="utf-8") as f:
            html_template = f.read()
    except FileNotFoundError:
        logger.error("No se encontró ficha_template.html")
        return None, None

    reemplazos = {
        "{{ FICHA_ID }}": ficha_id,
        "{{ IMAGEN_URL }}": imagen_publica,
        "{{ TITULO }}": titulo,
        "{{ PRECIO }}": precio,
        "{{ PRECIO_SUB }}": "Precio sujeto a cambios",
        "{{ DESCRIPCION }}": descripcion,
        "{{ UBICACION }}": ubicacion,
        "{{ DETALLES }}": detalles,
        "{{ FECHA }}": datetime.now().strftime("%d/%m/%Y"),
        "{{ AGENCIA }}": agencia,
        "{{ TELEGRAM_URL }}": telegram_url
    }

    html_final = html_template
    for k, v in reemplazos.items():
        html_final = html_final.replace(k, str(v or ""))

    ruta_html = os.path.join(carpeta, "index.html")
    with open(ruta_html, "w", encoding="utf-8") as f:
        f.write(html_final)

    logger.info("Ficha %s generada correctamente", ficha_id)
    return ficha_id, carpeta
    
# --------------------------
# MODO MANUAL (para pruebas)
# --------------------------
if __name__ == "__main__":
    url = input("Pegá la URL de la propiedad: ").strip()

    ficha_id, carpeta = crear_ficha(
    url,
    "https://t.me/PRUEBA_USUARIO",
    "AGENCIA PRUEBA"
)

    print("\n--- FICHA GENERADA ---")
    print("ID:", ficha_id)
    print("Carpeta:", carpeta)
    print("URL pública:")
    print(f"https://tierrasapiens.github.io/fichas-prop/fichas/{ficha_id}/")

# FIN.