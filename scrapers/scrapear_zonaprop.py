#---------------------
# scrapear_zonaprop.py. V 0.8.txt - G-15/12/25 con Playwright
#---------------------
import re
import time
from playwright.sync_api import sync_playwright

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
            # Lanzamos el navegador (Chromium) en modo headless (sin ventana)
            browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
            
            # Creamos un contexto simulando ser un navegador real para evitar bloqueos simples
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )
            
            page = context.new_page()
            
            # Bloquear carga de imágenes y fuentes para ahorrar memoria en Railway
            page.route("**/*.{png,jpg,jpeg,svg,css,woff,woff2}", lambda route: route.abort())

            # Ir a la web y esperar hasta que la red esté casi inactiva (significa que cargó)
            try:
                page.goto(url, timeout=60000, wait_until="domcontentloaded")
            except Exception as e:
                print(f"Alerta de tiempo de espera (pero seguimos): {e}")

            # Esperar un poco extra para asegurar que el JS de Zonaprop rellene los precios
            page.wait_for_timeout(4000) 

# --- 1. TITULO ---
            try:
                # Intentamos buscar el H1
                if page.locator("h1").count() > 0:
                    data["titulo"] = page.locator("h1").first.inner_text().strip()
            except Exception as e:
                print(f"Error Título: {e}")

# --- 2. PRECIO ---
            try:
                # Buscamos selectores comunes de precio en Zonaprop
                precio_loc = page.locator(".price-value span").first
                if precio_loc.count() > 0:
                    data["precio"] = precio_loc.inner_text().strip()
                else:
                    # Intento B: buscar en el texto general si falla el selector
                    content = page.content()
                    match = re.search(r"(USD|ARS)\s*([\d\.]+)", content)
                    if match:
                        data["precio"] = f"{match.group(1)} {match.group(2)}"
            except Exception as e:
                print(f"Error Precio: {e}")

            # --- 3. UBICACIÓN ---
            try:
                ubic_loc = page.locator(".section-location-property")
                if ubic_loc.count() > 0:
                    data["ubicacion"] = ubic_loc.inner_text().strip()
            except:
                pass

# --- 4. DESCRIPCIÓN ---
            try:
                ver_mas_desc = page.locator("#reactDescription button:has-text('Ver más'), #reactDescription .show-more").first
                
                if ver_mas_desc.count() > 0:
                    print(">>> Clic en 'Ver más' de la descripción.")
                    ver_mas_desc.click(force=True)
                    page.wait_for_timeout(500)
                
                # 4.2. Extraer el texto de la descripción
                desc_loc = page.locator("#reactDescription, .section-description").first
                
                if desc_loc.count() > 0:
                    texto = desc_loc.inner_text()
                    # Limpieza básica
                    cortes = ["Información importante", "Aviso publicado por"]
                    for c in cortes:
                        if c in texto:
                            texto = texto.split(c)[0]
                    data["descripcion"] = texto.strip()
                
            except Exception as e:
                # Si falla el clic, al menos intentamos obtener la descripción visible
                print(f"Error Descripción (al intentar clic): {e}")

                if desc_loc.count() > 0:
                    texto = desc_loc.first.inner_text()
                    # Limpieza básica
                    cortes = ["Información importante", "Aviso publicado por"]
                    for c in cortes:
                        if c in texto:
                            texto = texto.split(c)[0]
                    data["descripcion"] = texto.strip()
            except Exception as e:
                print(f"Error Descripción: {e}")

# --- 5. CARACTERÍSTICAS (Ambientes, m2, baños, etc.) ---
            data["caracteristicas"] = {}
            try:
                # Selector basado en la lista de iconos que muestra Zonaprop
                caracteristicas_ul = page.locator("#section-icon-features-property li.icon-feature")
                
                # Iteramos sobre cada elemento (li) encontrado
                for i in range(caracteristicas_ul.count()):
                    li = caracteristicas_ul.nth(i)
                    # Usamos inner_text() para obtener el texto del <li>
                    texto_li = li.inner_text().strip()
                    
                    if texto_li:
                        # 1. Intentamos obtener la clave usando las clases del ícono (más confiable)
                        clase_icono = li.locator("i").get_attribute("class")
                        
                        # Mapeo de Clases Zonaprop a Claves Legibles
                        clave = None
                        valor = ""
                        
                        # El texto_li puede ser '450 m² tot.' o 'Contrafrente'
                        partes_texto = texto_li.split()
                        
                        # Intenta extraer el valor (usando el primer elemento numérico si existe)
                        if partes_texto and partes_texto[0].isdigit():
                            valor = partes_texto[0]
                        
                        # --- Mapeo de Claves ---
                        if clase_icono:
                            if "icon-dormitorio" in clase_icono:
                                clave = "Dormitorios"
                            elif "icon-ambiente" in clase_icono:
                                clave = "Ambientes" # ¡Esto captura los ambientes que faltaban!
                            elif "icon-scubierta" in clase_icono:
                                clave = "Superficie Cubierta"
                            elif "icon-stotal" in clase_icono:
                                clave = "Superficie Total"
                            elif "icon-bano" in clase_icono:
                                clave = "Baños"
                            elif "icon-cochera" in clase_icono:
                                clave = "Cocheras"
                            elif "icon-antiguedad" in clase_icono:
                                clave = "Antigüedad (años)" # ¡Esto captura la antigüedad!
                            elif "icon-orientacion" in clase_icono or "icon-disposicion" in clase_icono:
                                clave = "Orientación/Disposición"
                                # Para orientación y disposición, el valor es todo el texto (ej: "Contrafrente")
                                valor = texto_li.replace("M.", "").strip() 
                        
                        
                        # Si encontramos una clave válida
                        if clave:
                            # Si es Orientación, guardamos el texto completo limpio
                            if clave == "Orientación/Disposición" or clave == "Antigüedad (años)":
                                # Simplificamos el valor para estos campos específicos
                                valor_limpio = texto_li.replace("m² tot.", "").replace("años", "").strip()
                                # A veces el valor está al final (ej: '45 años')
                                if partes_texto and partes_texto[0].isdigit():
                                    valor_limpio = ' '.join(partes_texto)
                                else:
                                    # Si no empieza con número (como 'Contrafrente'), toma todo el texto
                                    valor_limpio = texto_li
                                data["caracteristicas"][clave] = valor_limpio

                            # Si son numéricos, usamos el valor numérico
                            elif valor:
                                data["caracteristicas"][clave] = valor
                            
                            # Para campos que no tienen número inicial (ej: 'Muy luminoso'), ignora
                            
                            
            except Exception as e:
                print(f"Error al extraer características: {e}")
                pass

# --- 6. IMÁGENES (Sacamos las URL del código fuente) ---
            try:
                # Zonaprop suele tener las imágenes en un slider.
                # Playwright puede extraer los atributos 'src' de las etiquetas img
                imgs = page.locator("img").all()
                for img in imgs:
                    src = img.get_attribute("src")
                    if src and "zonapropcdn" in src and "static" not in src:
                        # Evitar duplicados y miniaturas muy chicas
                        if "360x266" in src: 
                            src = src.replace("360x266", "960x720") # Truco para alta calidad
                        if src not in data["imagenes"]:
                            data["imagenes"].append(src)
            except Exception as e:
                print(f"Error Imágenes: {e}")

            browser.close()

    except Exception as e:
        print(f"ERROR CRÍTICO EN PLAYWRIGHT: {e}")
    
    return data

# Bloque de prueba (solo si ejecutas este archivo directo)
if __name__ == "__main__":
    url_test = input("URL ZONAPROP: ")
    res = scrapear_zonaprop(url_test)
    print(res)