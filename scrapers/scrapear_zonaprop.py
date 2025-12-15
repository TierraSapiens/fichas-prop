#---------------------
# zonaprop.py V 0.9.6.txt - GyCH-14/12/25 "FUNCIONAl" 
#---------------------
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re
import json  # reservado

def scrapear_zonaprop(url):
    print(f"--- Iniciando scraping de: {url} ---")

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-logging")

    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    driver = webdriver.Chrome(options=options)
    driver.implicitly_wait(10)
    wait = WebDriverWait(driver, 15)

    data = {
        "titulo": "No encontrado",
        "precio": "Consultar",
        "ubicacion": "Ubicación no encontrada",
        "descripcion": "Sin descripción",
        "caracteristicas": {},
        "imagenes": []
    }

    try:
        driver.get(url)
        time.sleep(4)

        # ----------------
        # 1. TÍTULO
        # ----------------
        try:
            h1 = wait.until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
            data["titulo"] = h1.text.strip()
        except Exception as e:
            print(f"Error Título: {e}")

        driver.execute_script("window.scrollTo(0, 800)")
        time.sleep(1)

        # -------------------------------------------
        # 2. PRECIO (dataLayer → fallback HTML)
        # -------------------------------------------
        data["precio"] = "Consultar"

        scripts = driver.find_elements(By.TAG_NAME, "script")

        for s in scripts:
            js = s.get_attribute("innerHTML")
            if "precioVenta" in js:
                match = re.search(
                    r"'precioVenta'\s*:\s*\"([A-Z]{3})\s*([\d\.]+)\"",
                    js
                )
                if match:
                    moneda = match.group(1)
                    valor = match.group(2).replace(".", "")
                    data["precio"] = f"{moneda} {valor}"
                    break

        if data["precio"] == "Consultar":
            try:
                precio_elem = driver.find_element(By.CLASS_NAME, "price-value")
                texto = precio_elem.text
                match = re.search(r"(USD|ARS)\s*([\d\.]+)", texto)
                if match:
                    data["precio"] = f"{match.group(1)} {match.group(2)}"
            except:
                pass

        # ----------------
        # 3. UBICACIÓN
        # ----------------
        try:
            ubic_elem = driver.find_element(By.CLASS_NAME, "section-location-property")
            data["ubicacion"] = ubic_elem.text.strip()
        except:
            try:
                data["ubicacion"] = driver.find_element(
                    By.CSS_SELECTOR, "[data-qa='address']"
                ).text.strip()
            except:
                print("Error Ubicación")

        #------------------
        # 4. DESCRIPCION
        #------------------
        try:
            try:
                desc_elem = wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "#reactDescription .section-description")
                    )
                )
            except:
                desc_elem = wait.until(
                    EC.presence_of_element_located(
                        (By.ID, "reactDescription")
                    )
                )

            html = desc_elem.get_attribute("innerHTML")
            texto = re.sub(r"<br\s*/?>", "\n", html)
            texto = re.sub(r"<.*?>", "", texto)
            texto = re.sub(r"\n{3,}", "\n\n", texto)
            texto = texto.strip()

            cortes = [
                "Información importante",
                "El valor del inmueble puede ser modificado",
                "Las fotografías son propiedad",
                "La información gráfica y escrita",
                "Los impuestos, tasas"
            ]

            for c in cortes:
                if c in texto:
                    texto = texto.split(c)[0].strip()

            data["descripcion"] = texto if texto else "Sin descripción."

        except Exception as e:
            data["descripcion"] = "Sin descripción."
            print(f"Error Descripción: {e}")

        # -------------------------------------------
        # 5. CARACTERÍSTICAS
        # -------------------------------------------
        mapeo_claves = {
            "m² tot": "Superficie Total",
            "m² cub": "Superficie Cubierta",
            "amb": "Ambientes",
            "baños": "Baños",
            "dorm": "Dormitorios",
            "coch": "Cocheras",
            "años": "Antigüedad"
        }

        try:
            section = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "section-main-features"))
            )

            items = section.find_elements(By.CSS_SELECTOR, "li.icon-feature")

            for item in items:
                texto = item.text.lower().replace("\n", " ").strip()

                for clave_raw, clave_final in mapeo_claves.items():
                    if clave_raw in texto:
                        match = re.search(r"\d+", texto)
                        if match:
                            data["caracteristicas"][clave_final] = match.group()
                        break

        except Exception as e:
            print(f"Error Características: {e}")

        # ----------------
        # 6. IMÁGENES
        # ----------------
        try:
            imgs = driver.find_elements(By.TAG_NAME, "img")
            for img in imgs:
                src = img.get_attribute("src")
                if src and "zonapropcdn" in src and "static" not in src:
                    if src not in data["imagenes"]:
                        data["imagenes"].append(src)
        except Exception as e:
            print(f"Error Imágenes: {e}")

    except Exception as e:
        print(f"Error Crítico: {e}")

    finally:
        driver.quit()

    return data