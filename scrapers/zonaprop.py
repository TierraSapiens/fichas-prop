# ---------------------
# scrapers/zonaprop.py 1.6
# ---------------------

import requests
import re
from bs4 import BeautifulSoup

def scrapear_zonaprop(url):
    session = requests.Session()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "es-AR,es;q=0.9",
        "Referer": "https://www.zonaprop.com.ar/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    # 🔹 PRIMER REQUEST → setea cookies
    session.get("https://www.zonaprop.com.ar/", headers=headers, timeout=10)

    # 🔹 SEGUNDO REQUEST → propiedad
    r = session.get(url, headers=headers, timeout=15)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    data = {
        "titulo": "",
        "precio": "Consultar",
        "descripcion": "",
        "imagenes": []
    }

    # -----------------
    # TÍTULO
    # -----------------
    h1 = soup.select_one("h1.title-property")
    if h1:
        data["titulo"] = h1.get_text(strip=True)

    # -----------------
    # PRECIO (dataLayer JS)
    # -----------------
    m = re.search(r"precioVenta'\s*:\s*\"([^\"]+)\"", r.text)
    if m:
        data["precio"] = m.group(1)

    # -----------------
    # DESCRIPCIÓN
    # -----------------
    desc = soup.select_one(".section-description")
    if desc:
        data["descripcion"] = desc.get_text("\n", strip=True)

    # -----------------
    # IMÁGENES
    # -----------------
    imgs = soup.select("img[src*='imgar.zonapropcdn.com/avisos']")
    data["imagenes"] = list(dict.fromkeys(
        img["src"] for img in imgs if img.get("src")
    ))

    return data