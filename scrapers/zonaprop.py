#------------------
# zonaprop.py V 1.3 G 22/12/25 Muestra todo incluido descripcion completa pero sale el nombre inmobiliaria
#-------------------
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
        # Lanzamos navegador
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        async def block_assets(route):
            # Solo bloqueamos imágenes. Las fuentes y CSS los dejamos para que no se trabe.
            if route.request.resource_type == "image":
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", block_assets)

        try:
            await page.goto(url, timeout=45000, wait_until="domcontentloaded")
        except Exception as e:
            print(f"Aviso de carga rápida: {e}")

            # --- EXTRACCIÓN DE DATOS ---
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
            data["precio"] = (await precio.inner_text()).strip() if await precio.count() > 0 else "Consultar"

            # Ubicación
            ubic = page.locator(".section-location-property").first
            data["ubicacion"] = (await ubic.inner_text()).strip().replace("\n", " ") if await ubic.count() > 0 else "No encontrada"

            # Descripción
        try:
            # Intentamos expandir la descripción si existe el botón
            boton_leer_mas = page.locator("button:has-text('Leer descripción completa'), .show-more-button").first
            if await boton_leer_mas.is_visible():
              await boton_leer_mas.click()
              await asyncio.sleep(0.5) # Breve pausa para que el texto aparezca
            
            desc_element = page.locator("#reactDescription, .section-description").first
            if await desc_element.count() > 0:
                texto_sucio = await desc_element.inner_text()
                
                # 2. LISTA DE CORTE: Si aparece alguna de estas, cortamos el texto
                frases_a_cortar = [
                    "Aviso publicado por",
                    "Comercializa Spano Propiedades",
                    "Encontrá departamentos, casas, PH",
                    "Seguinos en nuestras redes",
                    "Asesoramiento personalizado para",
                    "@spanopropiedades"
                    "@"
                    "NOTA"
                    "Consultas"
                ]
                
                texto_limpio = texto_sucio
                for frase in frases_a_cortar:
                    if frase in texto_limpio:
                        # Cortamos y nos quedamos solo con lo que está ANTES de la frase
                        texto_limpio = texto_limpio.split(frase)[0]
                
                data["descripcion"] = texto_limpio.strip()

        except Exception as e:
            print(f"Error limpiando descripción: {e}")

            # Imágenes
            html_source = await page.content()
            fotos_encontradas = re.findall(r'https://imgar\.zonapropcdn\.com/avisos/[^"\'>]*\.jpg', html_source)
            
            fotos_unicas = []
            vistas = set()

            for f in fotos_encontradas:
                # Normalizamos TODAS las URLs a 960x720 antes de comparar
                # Esto es clave: si no las normalizás, el set no detecta que son la misma foto
                f_hd = re.sub(r'/\d+x\d+/', '/960x720/', f)
                
                if f_hd not in vistas:
                    vistas.add(f_hd)
                    fotos_unicas.append(f_hd)

            # Guardamos solo 5 para que el carrusel sea rápido
            data["imagenes"] = fotos_unicas[:5]
            
            # 1. Buscamos todas las URLs que coincidan con el patrón
            fotos_encontradas = re.findall(r'https://imgar\.zonapropcdn\.com/avisos/[^"\'>]*\.jpg', html_source)
            
            # 2. Usamos un set para eliminar duplicados exactos de inmediato
            fotos_unicas = []
            vistas = set()

            for f in fotos_encontradas:
                # Forzamos la resolución HD
                f_hd = re.sub(r'/\d+x\d+/', '/960x720/', f)
                
                # Solo la agregamos si no la vimos antes
                if f_hd not in vistas:
                    vistas.add(f_hd)
                    fotos_unicas.append(f_hd)

            # 3. Guardamos las primeras xx cantidad de fotos reales
            data["imagenes"] = fotos_unicas[:5]

        except Exception as e:
            print(f"Error extrayendo datos: {e}")

        await browser.close()
        print(">>> Scraping finalizado con éxito.")
        return data