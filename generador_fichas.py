# ----------------------------------
# Generador de Fichas con Imagen
# Versión Limpia 2025
# -----------------------------------

import os
import json
import random
import string
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# ---------------------------------------
# 1. Generar ID aleatorio (20 caracteres)
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


# -----------------------------------------------------
# 2. Extraer imagen principal usando OpenGraph
#    Funciona con: Zonaprop, Argenprop, Clarín, Properati
# -----------------------------------------------------
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
# 3. Descargar imagen dentro de la carpeta de la ficha
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
# 4. Crear estructura HTML y carpeta de la ficha
# ---------------------------------------------------------
def crear_ficha(url_propiedad):
    ficha_id = generar_id_unico()

    carpeta_ficha = os.path.join("fichas", ficha_id)
    os.makedirs(carpeta_ficha, exist_ok=True)

    # Obtener imagen principal
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

    html = f"""
<html>
<head>
<meta charset="utf-8">
<title>Propiedad — {ficha_id}</title>

<!-- Open Graph -->
<meta property="og:title" content="Encontré esta propiedad que te puede interesar">
<meta property="og:description" content="Haz clic para ver los detalles de la propiedad.">
<meta property="og:image" content="{url_publica_img}">
<meta property="og:url" content="https://tierrasapiens.github.io/fichas-prop/fichas/{ficha_id}/">
<meta property="og:type" content="article">

<style>
body {{
    font-family: Arial, sans-serif;
    background: #f4f4f4;
    margin: 0;
    padding: 20px;
}}
.contenedor {{
    max-width: 800px;
    margin: auto;
    background: #fff;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}}
.imagen {{
    width: 100%;
    border-radius: 10px;
    margin-bottom: 15px;
}}
h1 {{
    font-size: 26px;
    margin-bottom: 10px;
}}
</style>

</head>
<body>

<div class="contenedor">
    <img src="{url_publica_img}" class="imagen">
    <h1>Ficha de Propiedad</h1>
    <p><b>ID único:</b> {ficha_id}</p>
    <p><b>Fecha de creación:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    <p><b>Enlace original:</b><br><a href="{url_propiedad}">{url_propiedad}</a></p>
    <br><br>

<!-- BOTÓN DE CONTACTO POR TELEGRAM -->
<div style="margin-top: 25px; text-align: center;">
    <a href="https://t.me/Enrique_Mdq" target="_blank" 
       style="
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: #0088cc;
            color: white;
            padding: 14px 22px;
            border-radius: 10px;
            text-decoration: none;
            font-size: 18px;
            font-weight: bold;
       ">
        <img src="https://cdn-icons-png.flaticon.com/512/2111/2111646.png" 
             width="26" height="26">
        Contactar por Telegram
    </a>
</div>

</div>

</body>
</html>
"""

    with open(ruta_html, "w", encoding="utf-8") as f:
        f.write(html)

    return ficha_id, carpeta_ficha