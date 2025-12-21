#--------------------
# zonaprop.py V 1.1
#--------------------
import re
from playwright.async_api import async_playwright


async def scrapear_zonaprop(url: str) -> dict:
    print(f"--- Iniciando scraping con Playwright: {url} ---")

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
        browser = await p.chromium.launch(
            headless=True
            # si querés ver el browser:
            # headless=False, slow_mo=200
        )

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/119.0.0.0 Safari/537.36"
            )
        )

        page = await context.new_page()

        # Bloqueador de assets (dejamos CSS para que el 'Ver más' funcione)
        async def block_assets(route):
            if route.request.resource_type in ["image", "font", "media"]:
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", block_assets)

        try:
            # "commit" es la forma más rápida de entrar
            await page.goto(url, timeout=45000, wait_until="commit")
            # Esperamos solo a que el cuerpo de la página esté ahí
            await page.wait_for_selector("body", timeout=10000)
        except Exception as e:
            print("Aviso de carga:", e)

        # 1️⃣ TITULO
        try:
            h1 = page.locator("h1").first
            if await h1.count() > 0:
                data["titulo"] = (await h1.inner_text()).strip()
        except:
            pass

        # 2️⃣ PRECIO
        try:
            precio = page.locator(".price-value span").first
            if await precio.count() > 0:
                data["precio"] = (await precio.inner_text()).strip()
        except:
            pass

        # 3️⃣ UBICACION
        try:
            ubic = page.locator(".section-location-property")
            if await ubic.count() > 0:
                data["ubicacion"] = (
                    (await ubic.inner_text())
                    .strip()
                    .replace("\n", " ")
                )
        except:
            pass

        # 4️⃣ DESCRIPCION
        try:
            ver_mas = page.locator("button:has-text('Ver más'), .show-more").first
            if await ver_mas.is_visible():
                await ver_mas.click(force=True)
                await page.wait_for_timeout(500)

            desc = page.locator("#reactDescription, .section-description").first
            texto = await desc.inner_text()

            for corte in ["Información importante", "Aviso publicado por"]:
                if corte in texto:
                    texto = texto.split(corte)[0]

            data["descripcion"] = texto.strip()
        except:
            pass

        # 5️⃣ CARACTERISTICAS
        try:
            features = {}
            items = page.locator("li.icon-feature")
            count = await items.count()

            for i in range(count):
                li = items.nth(i)
                texto = (await li.inner_text()).strip()
                icon = await li.locator("i").get_attribute("class") or ""
                valor = texto.split("tot.")[0].split("cub.")[0].strip()

                if "icon-stotal" in icon:
                    features["Sup. Total"] = valor
                elif "icon-scubierta" in icon:
                    features["Sup. Cubierta"] = valor
                elif "icon-ambiente" in icon:
                    features["Ambientes"] = valor
                elif "icon-dormitorio" in icon:
                    features["Dormitorios"] = valor
                elif "icon-bano" in icon:
                    features["Baños"] = valor
                elif "icon-cochera" in icon:
                    features["Cocheras"] = valor
                elif "icon-antiguedad" in icon:
                    features["Antigüedad"] = valor

            data["caracteristicas"] = features
        except:
            pass

        # 6️⃣ IMAGENES - Versión Rayo
        try:
            # Obtenemos todo el código de la página de una vez
            contenido_html = await page.content()
            
            # Buscamos links que sigan el patrón de fotos de Zonaprop
            patron = r'https://imgar\.zonapropcdn\.com/avisos/[^"\'>]*\.jpg'
            links_hallados = re.findall(patron, contenido_html)
            
            fotos_finales = []
            for link in links_hallados:
                # Normalizamos todas a 960x720 (Alta Calidad)
                link_hd = re.sub(r'/\d+x\d+/', '/960x720/', link)
                if link_hd not in fotos_finales:
                    fotos_finales.append(link_hd)
            
            # Limitamos a 10 para que el JSON no sea pesado
            data["imagenes"] = fotos_finales[:10]
            
        except Exception as e:
            print(f"Error extrayendo imágenes: {e}")

    print("JSON SCRAPER:", data)
    return data