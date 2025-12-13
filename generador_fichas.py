# ------------------------------------------------------------
# generador_fichas.py V 1.2 —VERSIÓN CORREGIDA (import re + fixes)
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

# ------------------------------------------------------------
# Leer configuración general (agencia, título, etc.)
# ------------------------------------------------------------
def leer_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "agencia": "Ficha Prop"
        }

# ------------------------------------------------------------
# 1. Generar ID único
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# 2. Extraer datos OpenGraph (Título, Descripción, Imagen)
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# 3. "Descargar imagen" (Hasta ahora 0 exito.!!)
# ------------------------------------------------------------
def _extraer_url_imagen(soup):
    # intenta varias fuentes: og:image, link rel=image_src, img visible, srcset
    og = soup.find("meta", property="og:image")
    if og and og.get("content"):
        return og.get("content").strip()
    link_img = soup.find("link", rel="image_src")
    if link_img and link_img.get("href"):
        return link_img.get("href").strip()
    # buscar img principal (clásico)
    img = soup.find("img")
    if img:
        # priorizar src, luego data-src, luego srcset primera URL
        for attr in ("src", "data-src", "data-lazy-src"):
            u = img.get(attr)
            if u:
                return u
        srcset = img.get("srcset")
        if srcset:
            # tomar la primera url del srcset
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

        # resolver URL relativa si hace falta
        if pagina_base and not urllib.parse.urlparse(url_img).netloc:
            url_img = urllib.parse.urljoin(pagina_base, url_img)

        # reintentos simples
        for intento in range(2):
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                r = requests.get(url_img, headers=headers, timeout=timeout)
                r.raise_for_status()
                # componer nombre por extensión conocida
                ext = os.path.splitext(urllib.parse.urlparse(url_img).path)[1].lower()
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

# ------------------------------------------------------------
# 4. Crear ficha (HTML + imagen = 0 Exito.!!)
# ------------------------------------------------------------
def crear_ficha(url_propiedad):

# Leer configuración
    config = leer_config()
    agencia = config.get("agencia", "Ficha Prop")

    ficha_id = generar_id_unico()
    carpeta = os.path.join("fichas", ficha_id)
    os.makedirs(carpeta, exist_ok=True)

# Extraer datos OpenGraph
    titulo, descripcion, precio, imagen_url = extraer_datos_opengraph(url_propiedad)

# Imagen pública
    if imagen_url:
        if imagen_url:
            nombre_img = descargar_imagen(imagen_url, carpeta, pagina_base=url_propiedad)
            if nombre_img:
                imagen_publica = f"https://tierrasapiens.github.io/fichas-prop/fichas/{ficha_id}/{nombre_img}"
            else:
                imagen_publica = "https://tierrasapiens.github.io/fichas-prop/default.jpg"
    else:
        imagen_publica = "https://tierrasapiens.github.io/fichas-prop/default.jpg"

# Leer template
    try:
        with open("ficha_template.html", "r", encoding="utf-8") as f:
            html_template = f.read()
    except FileNotFoundError:
        raise FileNotFoundError("ERROR: Falta ficha_template.html en la carpeta raíz.")

# Reemplazar valores (Ojo: La plantilla debe usar estas Valores-llaves)
    reemplazos = {
    "{{ FICHA_ID }}": ficha_id,
    "{{ IMAGEN_URL }}": imagen_publica,
    "{{ TITULO }}": titulo,
    "{{ PRECIO }}": precio,
    "{{ DESCRIPCION }}": descripcion,
    "{{ FECHA }}": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "{{ AGENCIA }}": agencia
}

    html_final = html_template
    for k, v in reemplazos.items():
        html_final = html_final.replace(k, v)

# Guardar HTML
    ruta_html = os.path.join(carpeta, "index.html")
    with open(ruta_html, "w", encoding="utf-8") as f:
        f.write(html_final)

    return ficha_id, carpeta

# ------------------------------------------------------------
# MODO MANUAL (para pruebas)
# ------------------------------------------------------------
if __name__ == "__main__":
    url = input("Pegá la URL de la propiedad: ").strip()
    ficha_id, carpeta = crear_ficha(url)

    print("\n--- FICHA GENERADA ---")
    print("ID:", ficha_id)
    print("Carpeta:", carpeta)
    print("URL pública:")
    print(f"https://tierrasapiens.github.io/fichas-prop/fichas/{ficha_id}/")

# FIN.