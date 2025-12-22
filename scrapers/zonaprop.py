#------------------
# zonaprop.py V 1.2
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
            data["precio"] = (await precio.inner_text()).strip() if await precio.count() > 0 else "Consultar"

            # Ubicación
            ubic = page.locator(".section-location-property").first
            data["ubicacion"] = (await ubic.inner_text()).strip().replace("\n", " ") if await ubic.count() > 0 else "No encontrada"

            # Descripción
            desc = page.locator("#reactDescription, .section-description").first
            if await desc.count() > 0:
                data["descripcion"] = (await desc.inner_text()).split("Aviso publicado por")[0].strip()

            # Imágenes (Extracción desde el código fuente para máxima velocidad)
            html_source = await page.content()
            
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

            # 3. Guardamos las primeras 12 fotos reales (evitando logos de inmobiliarias si los hubiera)
            data["imagenes"] = fotos_unicas[:12]

        except Exception as e:
            print(f"Error extrayendo datos: {e}")

        await browser.close()
        print(">>> Scraping finalizado con éxito.")
        return data