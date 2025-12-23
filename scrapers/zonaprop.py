#---------------------
# zonaprop.py V 1.4.2
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

        async def block_assets(route):
            if route.request.resource_type == "image":
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", block_assets)

        try:
            await page.goto(url, timeout=45000, wait_until="domcontentloaded")
        except Exception as e:
            print(f"Aviso de carga rápida: {e}")

        # EXTRACCION DE DATOS
        try:
            # Titulo
            selectors_titulo = ["h1", ".title-type", ".section-title h1", "h2.title"]
            for selector in selectors_titulo:
                h1 = page.locator(selector).first
                if await h1.count() > 0:
                    texto = await h1.inner_text()
                    data["titulo"] = texto.strip()
                    break

            # Precio
            precio = page.locator(".price-value span").first
            data["precio"] = (await precio.inner_text()).strip() if await precio.count() > 0 else "Consultar"

            # Ubicacion
            ubic = page.locator(".section-location-property").first
            data["ubicacion"] = (await ubic.inner_text()).strip().replace("\n", " ") if await ubic.count() > 0 else "No encontrada"

            # Descripcion
            boton_leer_mas = page.locator("button:has-text('Leer descripción completa'), .show-more-button").first
            if await boton_leer_mas.is_visible():
                await boton_leer_mas.click()
                await asyncio.sleep(0.5) 
            
            desc_element = page.locator("#reactDescription, .section-description").first
            if await desc_element.count() > 0:
                texto_sucio = await desc_element.inner_text()
                
                # Cargar diccionario (SOLO si hay descripcion)
                try:
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    ruta_filtros = os.path.join(base_dir, "filtros.txt")

                    with open(ruta_filtros, "r", encoding="utf-8") as f:
                        frases_a_cortar = [line.strip() for line in f if line.strip()]
                except FileNotFoundError:
                    frases_a_cortar = ["Aviso publicado por"]

                # Aplicar corte
                texto_limpio = texto_sucio
                for frase in frases_a_cortar:
                    idx = texto_limpio.lower().find(frase.lower())
                    if idx != -1:
                        texto_limpio = texto_limpio[:idx]

                data["descripcion"] = texto_limpio.strip()
            # --------------------------------------

            # --- Imágenes (CORREGIDO Y ALINEADO) ---
            try:
                galeria_selector = "#pdp-gallery, .gallery-container, .react_pdp_gallery"
                
                # 1. Intento de espera controlada
                try:
                    await page.wait_for_selector(galeria_selector, timeout=5000)
                except:
                    print("Aviso: El contenedor de galería no apareció, usando fallback.")
                    pass 

                # 2. Localizar el elemento
                galeria_element = page.locator(galeria_selector).first
                
                # 3. Extraer HTML (o del contenedor o de toda la página)
                if await galeria_element.count() > 0:
                    html_fuente = await galeria_element.inner_html()
                else:
                    html_fuente = await page.content()

                # 4. Busqueda de URLs con Regex
                fotos_encontradas = re.findall(r'https://imgar\.zonapropcdn\.com/avisos/[^"\'>]*\.jpg', html_fuente)
                
                fotos_unicas = []
                vistas = set()

                for f in fotos_encontradas:
                    # Limpiamos y normalizamos
                    f_limpia = re.sub(r'/\d+x\d+/', '/960x720/', f).split('?')[0]
                    
                    if f_limpia not in vistas:
                        vistas.add(f_limpia)
                        fotos_unicas.append(f_limpia)

                # 5. Plan C: Si aún no hay fotos, buscamos en los scripts del fondo (JSON)
                if not fotos_unicas:
                    full_content = await page.content()
                    fotos_unicas = list(dict.fromkeys(re.findall(r'https://imgar\.zonapropcdn\.com/avisos/\d+/[^"]+960x720\.jpg', full_content)))

                data["imagenes"] = fotos_unicas[:8]

            except Exception as e:
                print(f"Error crítico en módulo de imágenes: {e}")
                data["imagenes"] = []

        except Exception as e:
            print(f"Error extrayendo datos: {e}")

        await browser.close()
        print(">>> Scraping finalizado con éxito.")
        return data