# bot.py - Versión Integrada
import os
import requests
import shutil
from datetime import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Importamos la función exacta de tu github_api.py V 0.4
from github_api import subir_ficha_a_github

# Configuración
NGROK_URL = "https://jamey-gamogenetic-incompliantly.ngrok-free.dev"
GITHUB_OWNER = "TierraSapiens"
GITHUB_REPO = "fichas-prop"

# Dialogo en Telegram
def start(update: Update, context: CallbackContext):
    user_name = update.message.from_user.first_name
    texto_bienvenida = (
        f"🏠 *¡Hola, {user_name}! Bienvenid@ a Ficha Prop.*\n\n"
        "Soy tu asistente para generar fichas web profesionales "
        "a partir de enlaces de Zonaprop.\n\n"
        "📌 *¿Cómo empezar?*\n"
        "Simplemente envíame el **link de la propiedad** que quieras convertir."
    )
    
    # Enviamos el mensaje con Markdown para que las negritas funcionen
    update.message.reply_text(texto_bienvenida, parse_mode='Markdown')

def procesar_enlace(update: Update, context: CallbackContext):
    url_propiedad = update.message.text
    user = update.message.from_user
    
    # 1. Feedback Visual Inicial
    msg_estado = update.message.reply_text("🔍 *Analizando enlace...*", parse_mode='Markdown')

    try:
        # 2. Paso del Scraper
        msg_estado.edit_text("⚙️ *Conectando con el servidor local...*\n(Extrayendo datos de Zonaprop ⏳)")
        res = requests.post(f"{NGROK_URL}/scrape/zonaprop", json={"url": url_propiedad}, timeout=60)
        resultado = res.json()

        if not resultado.get('ok'):
            return msg_estado.edit_text("❌ *Error:* No pudimos obtener los datos. Verificá que el link sea correcto.")

        # 3. Paso de Generación
        msg_estado.edit_text("🎨 *Generando diseño de ficha personalizada...*")
        data = resultado['data']
        
        # ... (aquí va tu lógica de generar_html y guardar carpeta temporal) ...
        
        # 4. Paso de Subida
        msg_estado.edit_text("🚀 *Publicando ficha en el servidor web...*")
        
        # ... (aquí va tu lógica de subir_ficha_a_github) ...

        # 5. Resultado Final con Formato Elegante
        link_web = f"https://{GITHUB_OWNER.lower()}.github.io/{GITHUB_REPO}/fichas/{ficha_id}/index.html"
        
        texto_final = (
            "✅ *¡Ficha generada con éxito!*\n\n"
            f"🏠 *Propiedad:* {data['titulo']}\n"
            f"💰 *Precio:* {data['precio']}\n\n"
            f"🌐 [VER FICHA ONLINE]({link_web})"
        )
        
        msg_estado.edit_text(texto_final, parse_mode='Markdown', disable_web_page_preview=False)

    except Exception as e:
        msg_estado.edit_text(f"⚠️ *Hubo un problema:* \n`{str(e)}`", parse_mode='Markdown')

def procesar_enlace(update: Update, context: CallbackContext):
    url_propiedad = update.message.text
    user = update.message.from_user
    
    update.message.reply_text("⏳ Conectando con tu PC local para scrapear... (30-40 seg)")

    try:
        # 1. PEDIR DATOS AL SCRAPER LOCAL (Paso 5 y 6)
        res = requests.post(f"{NGROK_URL}/scrape/zonaprop", json={"url": url_propiedad}, timeout=60)
        resultado = res.json()

        if not resultado.get('ok'):
            return update.message.reply_text("❌ El scraper local falló o no encontró la propiedad.")

        data = resultado['data']
        update.message.reply_text("📦 Datos recibidos. Generando ficha web...")

        # 2. CREAR CARPETA TEMPORAL (Paso 8)
        ficha_id = f"prop_{datetime.now().strftime('%H%M%S')}"
        carpeta_local = f"temp_{ficha_id}"
        os.makedirs(carpeta_local, exist_ok=True)

        # 3. GENERAR EL CONTACTO (Tu pedido: Teléfono/User del que pide)
        contacto_url = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user.id}"

        # 4. LEER Y REEMPLAZAR EN EL TEMPLATE
        with open('ficha_template.html', 'r', encoding='utf-8') as f:
            template = f.read()

        # Armamos los detalles en una lista simple para el HTML
        detalles_str = "".join([f"<li><strong>{k}:</strong> {v}</li>" for k, v in data['caracteristicas'].items()])

        html_final = template.replace("{{ TITULO }}", data['titulo']) \
                             .replace("{{ PRECIO }}", data['precio']) \
                             .replace("{{ UBICACION }}", data['ubicacion']) \
                             .replace("{{ DESCRIPCION }}", data['descripcion']) \
                             .replace("{{ IMAGEN_URL }}", data['imagenes'][0]) \
                             .replace("{{ TELEGRAM_URL }}", contacto_url) \
                             .replace("{{ DETALLES }}", f"<ul>{detalles_str}</ul>") \
                             .replace("{{ FICHA_ID }}", ficha_id) \
                             .replace("{{ AGENCIA }}", "Administración y Gestión")

        # Guardar index.html en la carpeta temporal
        with open(os.path.join(carpeta_local, "index.html"), "w", encoding='utf-8') as f:
            f.write(html_final)

        # 5. SUBIR A GITHUB (Paso 9)
        subir_ficha_a_github(ficha_id, carpeta_local)

        # 6. ENVIAR LINK FINAL
        link_web = f"https://{GITHUB_OWNER.lower()}.github.io/{GITHUB_REPO}/fichas/{ficha_id}/index.html"
        update.message.reply_text(f"✅ ¡Ficha publicada!\n\n🔗 Ver ficha: {link_web}")

        # Limpieza
        shutil.rmtree(carpeta_local)

    except Exception as e:
        update.message.reply_text(f"❌ Error crítico: {str(e)}")

# --- CONFIGURACIÓN DEL BOT ---
TOKEN_TELEGRAM = os.getenv("TELEGRAM_TOKEN") # Ponelo en Railway también
updater = Updater(TOKEN_TELEGRAM)
dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, procesar_enlace))

if __name__ == "__main__":
    updater.start_polling()
    updater.idle()