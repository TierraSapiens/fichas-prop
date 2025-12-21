# zonaprop.py V 1.3 (Anti-Detección Reforzado)
import re
import random
from playwright.async_api import async_playwright

async def scrapear_zonaprop(url: str) -> dict:
    print(f"--- Iniciando scraping (Modo Visual): {url} ---")

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
        # 1. LANZAMIENTO DEL NAVEGADOR
        # Usamos headless=False para que Zonaprop detecte GPU y renderizado real.
        # Esto abre la ventana de Chrome en tu PC (no la cierres, se cierra sola).
        browser = await p.chromium.launch(
            headless=False,  # <--- CAMBIO CLAVE: Ventana visible
            args=[
                '--disable-blink-features=AutomationControlled',
                '--start-maximized',
                '--no-sandbox',
                '--disable-infobars',
            ],
            ignore_default_args=["--enable-automation"] # Oculta la barra de "Chrome automatizado"
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={'width': 1366, 'height': 768},
            locale='es-AR'
        )

        page = await context.new_page()

        # Bloqueamos solo cosas muy pesadas, pero dejamos imagenes para parecer real
        # A veces bloquear todo alerta al sistema anti-bot.
        async def block_heavy_stuff(route):
            if route.request.resource_type in ["media", "font"]:
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", block_heavy_stuff)

        try:
            # 2. NAVEGACIÓN TÁCTICA
            # wait_until="commit" es instantáneo apenas conecta. No esperamos JS.
            await page.goto(url, timeout=40000, wait_until="commit")
            
            # Simulamos comportamiento humano (Mouse)
            # Esto dispara eventos que validan que no sos un robot
            await page.wait_for_timeout(2000) # Espera 2 seg
            await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
            await page.mouse.down()
            await page.mouse.up()
            
            # Esperamos específicamente el PRECIO o TITULO, no toda la página
            # Si aparece el precio, asumimos que cargó bien.
            await page.wait_for_selector(".price-value", timeout=10000)

        except Exception as e:
            print(f"⚠️ Alerta de carga: {e}")
            # Hacemos un screenshot si falla para que veas qué pasó (opcional)
            # await page.screenshot(path="error_debug.png")
            await browser.close()
            return data

        # --- EXTRACCIÓN DE DATOS ---
        
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
            ver_mas = page.locator("button:has-text('Ver más'), .show-more").first
            if await ver_mas.is_visible():
                await ver_mas.click(timeout=1000, force=True)
                await page.wait_for_timeout(500)
            
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

        # 6️ IMAGENES (Extracción HTML)
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
        except: pass

        await browser.close()
        
    print(f"✅ Scraping OK - Titulo: {data['titulo']}")
    return data