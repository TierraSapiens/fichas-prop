#---------------------
# zonaprop.py V 0.1 con Playwright
#---------------------
import re
import time
from playwright.sync_api import sync_playwright
from datetime import datetime

def scrapear_zonaprop(url):
    print(f"--- Iniciando scraping con Playwright: {url} ---")
    
    data = {
        "titulo": "No encontrado",
        "precio": "Consultar",
        "ubicacion": "Ubicación no encontrada",
        "descripcion": "Sin descripción",
        "caracteristicas": {},
        "imagenes": []
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox"
              ]
             )
            
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
            
            page = context.new_page()
            page.route("**/*.{png,jpg,jpeg,svg,css,woff,woff2}", lambda route: route.abort())

            try:
                page.goto(url, timeout=60000, wait_until="domcontentloaded")
            except Exception as e:
                print(f"Alerta de tiempo de espera (pero seguimos): {e}")

            page.wait_for_timeout(4000) 

            #1. TITULO
            try:
                if page.locator("h1").count() > 0:
                    data["titulo"] = page.locator("h1").first.inner_text().strip()
            except Exception as e:
                print(f"Error Título: {e}")

            #2. PRECIO
            try:
                precio_loc = page.locator(".price-value span").first
                if precio_loc.count() > 0:
                    data["precio"] = precio_loc.inner_text().strip()
                else:
                    content = page.content()
                    match = re.search(r"(USD|ARS)\s*([\d\.]+)", content)
                    if match:
                        data["precio"] = f"{match.group(1)} {match.group(2)}"
            except Exception as e:
                print(f"Error Precio: {e}")

            #3. UBICACION
            try:
                ubic_loc = page.locator(".section-location-property")
                if ubic_loc.count() > 0:
                    data["ubicacion"] = ubic_loc.inner_text().strip()
            except:
                pass

            #4. DESCRIPCION
            try:
                ver_mas_desc = page.locator("#reactDescription button:has-text('Ver más'), #reactDescription .show-more").first
                
                if ver_mas_desc.count() > 0:
                    print(">>> Clic en 'Ver más' de la descripción.")
                    ver_mas_desc.click(force=True)
                    page.wait_for_timeout(500)

                desc_loc = page.locator("#reactDescription, .section-description").first
                
                if desc_loc.count() > 0:
                    texto = desc_loc.inner_text()
                    cortes = ["Información importante", "Aviso publicado por"]
                    for c in cortes:
                        if c in texto:
                            texto = texto.split(c)[0]
                    data["descripcion"] = texto.strip()
                
            except Exception as e:
                print(f"Error Descripción (al intentar clic): {e}")

                if desc_loc.count() > 0:
                    texto = desc_loc.first.inner_text()
                    cortes = ["Información importante", "Aviso publicado por"]
                    for c in cortes:
                        if c in texto:
                            texto = texto.split(c)[0]
                    data["descripcion"] = texto.strip()
            except Exception as e:
                print(f"Error Descripción: {e}")

            #5. CARACTERISTICAS (Ambientes, m2, baños, etc.)
            data["caracteristicas"] = {}
            try:
                caracteristicas_ul = page.locator("#section-icon-features-property li.icon-feature")
                for i in range(caracteristicas_ul.count()):
                    li = caracteristicas_ul.nth(i)
                    texto_li = li.inner_text().strip()
                    if texto_li:
                        clase_icono = li.locator("i").get_attribute("class")
                        
                        clave = None
                        valor = ""
                        
                        partes_texto = texto_li.split()
                        
                        if partes_texto and partes_texto[0].isdigit():
                            valor = partes_texto[0]
                        
                        # Mapeo de Claves
                        if clase_icono:
                            if "icon-dormitorio" in clase_icono:
                                clave = "Dormitorios"
                            elif "icon-ambiente" in clase_icono:
                                clave = "Ambientes"
                            elif "icon-scubierta" in clase_icono:
                                clave = "Superficie Cubierta"
                            elif "icon-stotal" in clase_icono:
                                clave = "Superficie Total"
                            elif "icon-bano" in clase_icono:
                                clave = "Baños"
                            elif "icon-cochera" in clase_icono:
                                clave = "Cocheras"
                            elif "icon-antiguedad" in clase_icono:
                                clave = "Antigüedad (años)"
                            elif "icon-orientacion" in clase_icono or "icon-disposicion" in clase_icono:
                                clave = "Orientación/Disposición"
                                valor = texto_li.replace("M.", "").strip() 
                        
                        if clave:
                            if clave == "Orientación/Disposición" or clave == "Antigüedad (años)":
                                valor_limpio = texto_li.replace("m² tot.", "").replace("años", "").strip()
                                if partes_texto and partes_texto[0].isdigit():
                                    valor_limpio = ' '.join(partes_texto)
                                else:
                                    valor_limpio = texto_li
                                data["caracteristicas"][clave] = valor_limpio

                            elif valor:
                                data["caracteristicas"][clave] = valor          
                            
            except Exception as e:
                print(f"Error al extraer características: {e}")
                pass

            # 6. IMAGENES (URL del código fuente)
            try:
                imgs = page.locator("img").all()
                for img in imgs:
                    src = img.get_attribute("src")
                    if src and "zonapropcdn" in src and "static" not in src:
                        if "360x266" in src: 
                            src = src.replace("360x266", "960x720")
                        if src not in data["imagenes"]:
                            data["imagenes"].append(src)
            except Exception as e:
                print(f"Error Imágenes: {e}")

            browser.close()

    except Exception as e:
        print(f"ERROR CRÍTICO EN PLAYWRIGHT: {e}")

    return normalizar_zonaprop(data, url)

def normalizar_zonaprop(data, url):
    precio_valor = None
    precio_moneda = "ARS"

    precio_raw = data.get("precio", "")
    if isinstance(precio_raw, str):
        m = re.search(r"(USD|ARS)\s*([\d\.]+)", precio_raw.replace(",", ""))
        if m:
            precio_moneda = m.group(1)
            try:
                precio_valor = int(m.group(2).replace(".", ""))
            except:
                precio_valor = None

    ubicacion_raw = data.get("ubicacion", "")

    ubicacion = {
        "direccion": ubicacion_raw,
        "barrio": "",
        "ciudad": "",
        "provincia": ""
    }

    car = data.get("caracteristicas", {})

    def num(clave):
        try:
            return int(car.get(clave))
        except:
            return None

    caracteristicas = {
        "ambientes": num("Ambientes"),
        "dormitorios": num("Dormitorios"),
        "banios": num("Baños"),
        "superficie_m2": num("Superficie Total") or num("Superficie Cubierta")
    }
    
    print("JSON SCRAPER:", data)

    return {
        "fuente": "zonaprop",
        "url": url,
        "titulo": data.get("titulo", ""),
        "precio": {
            "valor": precio_valor,
            "moneda": precio_moneda
        },
        "ubicacion": ubicacion,
        "caracteristicas": caracteristicas,
        "descripcion": data.get("descripcion", ""),
        "imagenes": data.get("imagenes", []),
        "metadata": {
            "scraped_at": datetime.utcnow().isoformat(),
            "scraper_version": "1.0"
        }
    }