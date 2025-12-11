# ----------------------------------
# Generador de Fichas con Imagen V ¿? perdi la cuenta!
# -----------------------------------

import os
import json
import random
import string
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# ---------------------------------------
# 1- Generar ID aleatorio (20 caracteres)
# ----------------------------------------
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


# -------------------------------------------------------
# 2- Extraer imagen principal usando OpenGraph
# Funciona con: Zonaprop, Argenprop, Clarín, Properati....
# -------------------------------------------------------
def obtener_imagen_principal(url):
    """
    Devuelve la URL de la imagen principal desde OG:image.
    Esto funciona en casi todos los portales inmobiliarios.
    """

    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    og_img = soup.find("meta", property="og:image")
    if og_img and og_img.get("content"):
        return og_img["content"]

    return None

# ---------------------------------------------------------
# 3-Descargar imagen dentro de la carpeta de la ficha
# ---------------------------------------------------------
def descargar_imagen(url_img, carpeta_ficha):
    try:
        response = requests.get(url_img, timeout=10)
        response.raise_for_status()

        ruta = os.path.join(carpeta_ficha, "foto.jpg")
        with open(ruta, "wb") as f:
            f.write(response.content)

        return "foto.jpg"

    except Exception:
        return None

# ---------------------------------------------------------
# 4- Crear estructura HTML y carpeta de la ficha
# ---------------------------------------------------------
def crear_ficha(url_propiedad):
    ficha_id = generar_id_unico()

    carpeta_ficha = os.path.join("fichas", ficha_id)
    os.makedirs(carpeta_ficha, exist_ok=True)

# Obtener una imagen principal (¡Con problemas!)
    imagen_url = obtener_imagen_principal(url_propiedad)

    if imagen_url:
        nombre_imagen = descargar_imagen(imagen_url, carpeta_ficha)
        if nombre_imagen:
            url_publica_img = f"https://tierrasapiens.github.io/fichas-prop/fichas/{ficha_id}/{nombre_imagen}"
        else:
            url_publica_img = "https://tierrasapiens.github.io/fichas-prop/default.jpg"
    else:
        url_publica_img = "https://tierrasapiens.github.io/fichas-prop/default.jpg"

    ruta_html = os.path.join(carpeta_ficha, "index.html")

# INICIO NUEVO BLOQUE DE CÓDIGO (Reemplaza el antiguo bloque HTML aquí)
    try:
        with open("ficha_template.html", "r", encoding="utf-8") as f:
            html_template = f.read()
    except FileNotFoundError:
        raise FileNotFoundError("Error: No se encontró ficha_template.html en el directorio raíz.")

    reemplazos = {
        "{{ FICHA_ID }}": ficha_id,
        "{{ IMAGEN_URL }}": url_publica_img,
        "{{ FECHA_CREACION }}": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "{{ URL_ORIGINAL }}": url_propiedad,
    }

    html_final = html_template
    for placeholder, valor in reemplazos.items():
        html_final = html_final.replace(placeholder, valor)

    with open(ruta_html, "w", encoding="utf-8") as f:
        f.write(html_final)
    
    return ficha_id, carpeta_ficha