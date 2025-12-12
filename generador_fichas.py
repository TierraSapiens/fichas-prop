# ------------------------------------------------------------
# generador_fichas.py V 1.2 — ChatGpt VERSIÓN CORREGIDA (import re + fixes)
# ------------------------------------------------------------

import os
import json
import random
import string
import re
from datetime import datetime
import requests
from bs4 import BeautifulSoup

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
        # Si falla la petición, devolvemos valores por defecto
        return "Propiedad en venta / alquiler", "Sin descripción disponible.", "Consultar", None

    def og(prop):
        tag = soup.find("meta", property=f"og:{prop}")
        return tag.get("content").strip() if tag and tag.get("content") else None

    titulo = og("title") or "Propiedad en venta / alquiler"
    descripcion = og("description") or "Sin descripción disponible."
    imagen = og("image")

    # -------------------------------------------
    # Intento detectar un precio desde título o descripción
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
# 3. Descargar imagen
# ------------------------------------------------------------
def descargar_imagen(url_img, carpeta_ficha):
    try:
        r = requests.get(url_img, timeout=10)
        r.raise_for_status()

        ruta = os.path.join(carpeta_ficha, "foto.jpg")
        with open(ruta, "wb") as f:
            f.write(r.content)

        return "foto.jpg"
    except Exception:
        return None

# ------------------------------------------------------------
# 4. Crear ficha (HTML + imagen)
# ------------------------------------------------------------
def crear_ficha(url_propiedad):

    ficha_id = generar_id_unico()
    carpeta = os.path.join("fichas", ficha_id)
    os.makedirs(carpeta, exist_ok=True)

    # Extraer datos OpenGraph
    titulo, descripcion, precio, imagen_url = extraer_datos_opengraph(url_propiedad)

    # Imagen pública
    if imagen_url:
        nombre_img = descargar_imagen(imagen_url, carpeta)
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

    # Reemplazar valores (plantilla debe usar estas llaves)
    reemplazos = {
        "{{ FICHA_ID }}": ficha_id,
        "{{ IMAGEN_URL }}": imagen_publica,
        "{{ TITULO }}": titulo,
        "{{ PRECIO }}": precio,
        "{{ DESCRIPCION }}": descripcion,
        "{{ FECHA }}": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    html_final = html_template
    for k, v in reemplazos.items():
        html_final = html_final.replace(k, v)

    # Guardar HTML
    ruta_html = os.path.join(carpeta, "index.html")
    with open(ruta_html, "w", encoding="utf-8") as f:
        f.write(html_final)

    return ficha_id, carpeta