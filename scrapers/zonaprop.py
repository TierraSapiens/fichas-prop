# zonaprop.py V 1.2 (Optimizado)
import re
from playwright.async_api import async_playwright

async def scrapear_zonaprop(url: str) -> dict:
    print(f"--- Iniciando scraping optimizado: {url} ---")

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
        # Lanzamos con argumentos anti-detección
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 800}
        )

        page = await context.new_page()

        # Bloqueador de assets agresivo para ganar velocidad
        async def block_assets(route):
            if route.request.resource_type in ["image", "media", "font", "stylesheet"]:
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", block_assets)

        try:
            # Bajamos el timeout a 30s. Si no carga en 30s, no va a cargar.
            # wait_until="domcontentloaded" es más rápido que esperar toda la red.
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            
            # Esperamos un selector clave, pero solo 5 segundos
            await page.wait_for_selector("h1", timeout=5000) 
        except Exception as e:
            print(f"⚠️ Alerta de carga (posible bloqueo o lentitud): {e}")
            # Si falla la carga, cerramos y devolvemos lo que haya (o error)
            await browser.close()
            return data

        # --- EXTRACCIÓN (Igual que antes, pero protegida) ---
        
        # 1️ TITULO
        try:
            h1 = page.locator("h1").first
            if await h1.count() > 0:
                data["titulo"] = (await h1.inner_text()).strip()
        except: pass

        # 2️ PRECIO
        try:
            precio = page.locator(".price-value span").first
            if await precio.count() > 0:
                data["precio"] = (await precio.inner_text()).strip()
        except: pass

        # 3️ UBICACION
        try:
            ubic = page.locator(".section-location-property")
            if await ubic.count() > 0:
                data["ubicacion"] = (await ubic.inner_text()).strip().replace("\n", " ")
        except: pass

        # 4️ DESCRIPCION
        try:
            # Intentamos clickear ver más, pero con timeout corto
            ver_mas = page.locator("button:has-text('Ver más'), .show-more").first
            if await ver_mas.is_visible():
                await ver_mas.click(timeout=2000, force=True)
            
            desc = page.locator("#reactDescription, .section-description").first
            texto = await desc.inner_text()
            for corte in ["Información importante", "Aviso publicado por"]:
                if corte in texto: texto = texto.split(corte)[0]
            data["descripcion"] = texto.strip()
        except: pass

        # 5️ CARACTERISTICAS
        try:
            features = {}
            items = page.locator("li.icon-feature")
            count = await items.count()
            for i in range(count):
                li = items.nth(i)
                texto = (await li.inner_text()).strip()
                icon = await li.locator("i").get_attribute("class") or ""
                valor = texto.split("tot.")[0].split("cub.")[0].strip()

                if "icon-stotal" in icon: features["Sup. Total"] = valor
                elif "icon-scubierta" in icon: features["Sup. Cubierta"] = valor
                elif "icon-ambiente" in icon: features["Ambientes"] = valor
                elif "icon-dormitorio" in icon: features["Dormitorios"] = valor
                elif "icon-bano" in icon: features["Baños"] = valor
                elif "icon-cochera" in icon: features["Cocheras"] = valor
                elif "icon-antiguedad" in icon: features["Antigüedad"] = valor
            data["caracteristicas"] = features
        except: pass

        # 6️ IMAGENES (Extracción por HTML crudo, es más rápido)
        try:
            contenido_html = await page.content()
            patron = r'https://imgar\.zonapropcdn\.com/avisos/[^"\'>]*\.jpg'
            links_hallados = re.findall(patron, contenido_html)
            fotos_finales = []
            for link in links_hallados:
                link_hd = re.sub(r'/\d+x\d+/', '/960x720/', link)
                if link_hd not in fotos_finales:
                    fotos_finales.append(link_hd)
            data["imagenes"] = fotos_finales[:10]
        except Exception as e:
            print(f"Error imagenes: {e}")

        await browser.close()
        
    print("✅ Scraping finalizado con éxito")
    return data