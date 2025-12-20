import requests
from generador_fichas import generar_html_ficha
from github_api import subir_a_github # Asumiendo que tenés este script

NGROK_URL = "https://jamey-gamogenetic-incompliantly.ngrok-free.dev"

def manejar_mensaje(update, context):
    url_propiedad = update.message.text
    user = update.message.from_user
    
    update.message.reply_text("⏳ Procesando propiedad en tu PC local... esto demora unos 30s.")

    try:
        # 1. Pedir el scraping a tu PC (Paso 5)
        res = requests.post(f"{NGROK_URL}/scrape/zonaprop", json={"url": url_propiedad}, timeout=60)
        scraper_data = res.json()

        if scraper_data.get('ok'):
            # 2. Generar el HTML con los datos (Paso 8)
            info_usuario = {"username": user.username, "id": user.id}
            html_final = generar_html_ficha(scraper_data['data'], info_usuario)

            # 3. Subir a GitHub Pages (Paso 9)
            # Aquí usarías tu github_api.py para crear el archivo en la carpeta /fichas/
            nombre_archivo = f"ficha_{datetime.now().timestamp()}.html"
            link_publico = subir_a_github(html_final, nombre_archivo)

            update.message.reply_text(f"✅ ¡Ficha lista! Podés verla y compartirla aquí:\n{link_publico}")
        else:
            update.message.reply_text("❌ Error en el scraper local.")

    except Exception as e:
        update.message.reply_text(f"❌ Error de conexión: {str(e)}")