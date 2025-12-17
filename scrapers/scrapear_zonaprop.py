#---------------------
# scrapear_zonaprop.py. V 1.0.txt - CON MANEJO DE ERRORES ROBUSTO
#---------------------
import re
import logging
from playwright.sync_api import sync_playwright, TimeoutError, Error as PlaywrightError

# Configuración de Logging
logger = logging.getLogger(__name__)

# --- Selectores (Ajusta estos si Zonaprop los cambia) ---
# Usamos selectores CSS robustos que parecen funcionar
SELECTOR_TITULO = "h1"
SELECTOR_PRECIO = ".price-value span"
SELECTOR_UBICACION = ".section-location-property"
SELECTOR_DESCRIPCION = "#reactDescription, .section-description"
SELECTOR_CARACTERISTICAS = "#section-icon-features-property li.icon-feature"
# --------------------------------------------------------


def scrapear_zonaprop(url):
    """
    Scraper para Zonaprop usando Playwright.
    """
    logger.info(f"--- Iniciando scraping con Playwright: {url} ---")
    
    # Datos por defecto en caso de fallo parcial
    data = {
        "titulo": "No encontrado",
        "precio": "Consultar",
        "ubicacion": "Ubicación no encontrada",
        "descripcion": "Sin descripción",
        "caracteristicas": {},
        "imagenes": []
    }

    # Usamos sync_playwright para que se ejecute en el thread de asyncio.run_in_executor
    with sync_playwright() as p:
        browser = None
        try:
            # 1. LANZAR BROWSER
            browser = p.chromium.launch(
                headless=True,
                # Argumentos necesarios para funcionar en entornos como Railway
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox"
                ]
            )
            
            # 2. CREAR CONTEXTO Y PÁGINA (Añadir User-Agent para anti-bloqueo)
            page = browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Bloquear recursos innecesarios para ahorrar tiempo/memoria
            page.route("**/*.{png,jpg,jpeg,svg,css,woff,woff2}", lambda route: route.abort())

            # 3. NAVEGACIÓN
            logger.info("Navegando a la URL con 60s de timeout.")
            page.goto(url, timeout=60000, wait_until="domcontentloaded")
            
            # Esperar un poco extra para la carga de JS
            page.wait_for_timeout(4000) 

            # --- 4. EXTRACCIÓN DE DATOS ---

            # 4.1. TITULO
            try:
                # Esperamos explícitamente el selector principal (30 segundos)
                page.wait_for_selector(SELECTOR_TITULO, timeout=30000)
                if page.locator(SELECTOR_TITULO).count() > 0:
                    data["titulo"] = page.locator(SELECTOR_TITULO).first.inner_text().strip()
            except PlaywrightError:
                # Si falla aquí, no es crítico, seguimos
                logger.warning("No se pudo extraer el Título.")
                pass
            
            # 4.2. PRECIO
            try:
                precio_loc = page.locator(SELECTOR_PRECIO).first
                if precio_loc.count() > 0:
                    data["precio"] = precio_loc.inner_text().strip()
                # Fallback de RegExp (opcional, pero útil)
                elif data["precio"] == "Consultar":
                    content = page.content()
                    match = re.search(r"(USD|ARS|U\$S)\s*([\d\.,]+)", content, re.IGNORECASE)
                    if match:
                        data["precio"] = f"{match.group(1)} {match.group(2)}"
            except PlaywrightError:
                logger.warning("No se pudo extraer el Precio.")
                pass

            # 4.3. UBICACIÓN
            try:
                ubic_loc = page.locator(SELECTOR_UBICACION).first
                if ubic_loc.count() > 0:
                    data["ubicacion"] = ubic_loc.inner_text().strip()
            except PlaywrightError:
                logger.warning("No se pudo extraer la Ubicación.")
                pass

            # 4.4. DESCRIPCIÓN (Incluye intento de 'Ver más')
            try:
                # Intento de clic en "Ver más"
                ver_mas_desc = page.locator("#reactDescription button:has-text('Ver más'), #reactDescription .show-more").first
                if ver_mas_desc.count() > 0:
                    logger.info(">>> Clic en 'Ver más' de la descripción.")
                    ver_mas_desc.click(force=True)
                    page.wait_for_timeout(500) # Espera post-clic
                
                # Extraer el texto completo
                desc_loc = page.locator(SELECTOR_DESCRIPCION).first
                if desc_loc.count() > 0:
                    texto = desc_loc.inner_text()
                    cortes = ["Información importante", "Aviso publicado por"]
                    for c in cortes:
                        if c in texto:
                            texto = texto.split(c)[0]
                    data["descripcion"] = texto.strip()
            except PlaywrightError as e:
                logger.warning(f"Error al procesar Descripción: {e}")
                # Intentamos la extracción directa si el clic falla
                desc_loc = page.locator(SELECTOR_DESCRIPCION).first
                if desc_loc.count() > 0:
                    data["descripcion"] = desc_loc.inner_text().strip()

            # 4.5. CARACTERÍSTICAS
            data["caracteristicas"] = {}
            try:
                # Lógica de extracción de características basada en íconos
                caracteristicas_ul = page.locator(SELECTOR_CARACTERISTICAS)
                mapeo = {
                    "icon-dormitorio": "Dormitorios",
                    "icon-ambiente": "Ambientes",
                    "icon-scubierta": "Superficie Cubierta",
                    "icon-stotal": "Superficie Total",
                    "icon-bano": "Baños",
                    "icon-cochera": "Cocheras",
                    "icon-antiguedad": "Antigüedad (años)",
                }
                
                for i in range(caracteristicas_ul.count()):
                    li = caracteristicas_ul.nth(i)
                    texto_li = li.inner_text().strip()
                    clase_icono = li.locator("i").get_attribute("class")
                    
                    clave = None
                    for cls, k in mapeo.items():
                        if clase_icono and cls in clase_icono:
                            clave = k
                            break
                    
                    if clave:
                        # Para Orientación/Disposición, usamos el texto completo
                        if "orientacion" in clase_icono or "disposicion" in clase_icono:
                            valor = texto_li
                        else:
                            # Para el resto, extraemos el valor numérico (o el texto completo si es necesario)
                            valor = texto_li.split()[0] if texto_li.split() and texto_li.split()[0].isdigit() else texto_li
                        
                        data["caracteristicas"][clave] = valor.strip()
                        
            except PlaywrightError as e:
                logger.warning(f"Error al extraer características: {e}")
                pass
            
            # 4.6. IMÁGENES
            try:
                # Buscamos URLs de alta calidad
                imgs = page.locator("img").all()
                for img in imgs:
                    src = img.get_attribute("src")
                    if src and "zonapropcdn" in src and "static" not in src:
                        if "360x266" in src: 
                            src = src.replace("360x266", "960x720") 
                        if src not in data["imagenes"]:
                            data["imagenes"].append(src)
            except PlaywrightError as e:
                logger.warning(f"Error al extraer imágenes: {e}")
                pass
            
            # 5. RETORNO DE DATOS
            return data

        except PlaywrightError as e:
            # --- CAPTURA DE ERRORES CRÍTICOS DE PLAYWRIGHT ---
            # Si el navegador se cierra o hay un error de protocolo (bloqueo/fallo de red)
            logger.exception("FALLO CRÍTICO DE PLAYWRIGHT: Revisar si hay bloqueo o selector obsoleto.")
            raise # ¡VITAL! Re-lanza la excepción para que el bot.py registre el Traceback.

        except Exception as e:
            # --- CAPTURA DE CUALQUIER OTRO ERROR ---
            logger.exception("ERROR DESCONOCIDO EN EL SCRAPER.")
            raise # ¡VITAL! Re-lanza la excepción.
            
        finally:
            if browser:
                browser.close()

# Bloque de prueba (solo si ejecutas este archivo directo)
if __name__ == "__main__":
    url_test = input("URL ZONAPROP: ")
    res = scrapear_zonaprop(url_test)
    print(res)