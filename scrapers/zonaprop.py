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
            await page.goto(url, timeout=25000, wait_until="domcontentloaded")
        except Exception as e:
            print(f"Aviso de carga rápida: {e}")

        # --- EXTRACCIÓN DE DATOS ---
        try:
            # Título
            h1 = page.locator("h1").first
            data["titulo"] = (await h1.inner_text()).strip() if await h1.count() > 0 else "No encontrado"

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
            fotos = re.findall(r'https://imgar\.zonapropcdn\.com/avisos/[^"\'>]*\.jpg', html_source)
            # Limpiamos, forzamos HD y quitamos duplicados
            fotos_hd = []
            for f in fotos:
                f_clean = re.sub(r'/\d+x\d+/', '/960x720/', f)
                if f_clean not in fotos_hd:
                    fotos_hd.append(f_clean)
            data["imagenes"] = fotos_hd[:12] # Limitamos a 12 para el carrusel

        except Exception as e:
            print(f"Error extrayendo datos: {e}")

        await browser.close()
        print(">>> Scraping finalizado con éxito.")
        return data