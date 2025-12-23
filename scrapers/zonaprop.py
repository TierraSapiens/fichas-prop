#---------------------
# zonaprop.py V 1.4.4
#---------------------
import os
import re
import asyncio
from playwright.async_api import async_playwright

async def scrapear_zonaprop(url: str) -> dict:
    print(f"--- Iniciando scraping manual: {url} ---")

    data = {
        "fuente": "zonaprop",
        "url": url,
        "titulo": "No encontrado",
        "precio": "Consultar",
        "ubicacion": "Ubicación no encontrada",
        "descripcion": "Sin descripción",
        "caracteristicas": {},
        "imagenes": []
    }

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        try:
            # Usamos "commit" para velocidad, pero esperamos al H1 para asegurar contenido
            await page.goto(url, timeout=45000, wait_until="commit")
            await page.wait_for_selector("h1", timeout=10000)
        except Exception as e:
            print(f"Aviso de carga: {e}")

        # --- EXTRACCIÓN DE DATOS TEXTUALES ---
        try:
            # Título
            selectors_titulo = ["h1", ".title-type", ".section-title h1", "h2.title"]
            for selector in selectors_titulo:
                h1 = page.locator(selector).first
                if await h1.count() > 0:
                    texto = await h1.inner_text()
                    data["titulo"] = texto.strip()
                    break

            # Precio
            precio = page.locator(".price-value span").first
            if await precio.count() > 0:
                data["precio"] = (await precio.inner_text()).strip()

            # Ubicación
            ubic = page.locator(".section-location-property").first
            if await ubic.count() > 0:
                data["ubicacion"] = (await ubic.inner_text()).strip().replace("\n", " ")

            # Descripción y Filtros
            boton_leer_mas = page.locator("button:has-text('Leer descripción completa'), .show-more-button").first
            if await boton_leer_mas.is_visible():
                await boton_leer_mas.click()
                await asyncio.sleep(0.5) 
            
            desc_element = page.locator("#reactDescription, .section-description").first
            if await desc_element.count() > 0:
                texto_sucio = await desc_element.inner_text()
                
                # Cargar diccionario de filtros
                try:
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    ruta_filtros = os.path.join(base_dir, "filtros.txt")
                    with open(ruta_filtros, "r", encoding="utf-8") as f:
                        frases_a_cortar = [line.strip() for line in f if line.strip()]
                except FileNotFoundError:
                    frases_a_cortar = ["Aviso publicado por"]

                # Aplicar guillotina de texto
                texto_limpio = texto_sucio
                for frase in frases_a_cortar:
                    idx = texto_limpio.lower().find(frase.lower())
                    if idx != -1:
                        texto_limpio = texto_limpio[:idx]

                data["descripcion"] = texto_limpio.strip()

        except Exception as e:
            print(f"Error extrayendo textos: {e}")

        # --- EXTRACCIÓN DE IMÁGENES (ID ÚNICO) ---
        try:
            # Intentamos aislar la galería principal
            galeria = page.locator(".preview-gallery-module__grid-layout___Mqd-2, .re-cluster-container").first
            if await galeria.count() > 0:
                html_fuente = await galeria.inner_html()
            else:
                html_fuente = await page.content()

            urls_crudas = re.findall(r'https://imgar\.zonapropcdn\.com/avisos/[^"\'>]*\.jpg', html_fuente)
            
            fotos_limpias = []
            ids_vistos = set()

            for url in urls_crudas:
                # Extraer el ID numérico antes del .jpg
                match_id = re.search(r'/(\d+)\.jpg', url)
                if match_id:
                    foto_id = match_id.group(1)
                    
                    if foto_id not in ids_vistos:
                        ids_vistos.add(foto_id)
                        
                        # Limpiar URL y forzar HD
                        url_hd = url.split('?')[0]
                        url_hd = re.sub(r'/resize/\d+/\d+/\d+/\d+/\d+/', '/', url_hd)
                        url_hd = re.sub(r'/\d+x\d+/', '/960x720/', url_hd)
                        
                        fotos_limpias.append(url_hd)

            data["imagenes"] = fotos_limpias[:5]

        except Exception as e:
            print(f"Error en módulo de imágenes: {e}")

        await browser.close()
        print(f">>> Scraping finalizado. Fotos únicas: {len(data['imagenes'])}")
        return data