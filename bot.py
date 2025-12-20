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

def start(update: Update, context: CallbackContext):
    user_name = update.message.from_user.first_name
    texto_bienvenida = (
        f"🏠 *¡Hola, {user_name}! Bienvenid@ a Ficha Prop.*\n\n"
        "Soy tu asistente para generar fichas web profesionales.\n"
        "Enviame el **link de Zonaprop** para empezar."
    )
    update.message.reply_text(texto_bienvenida, parse_mode='Markdown')

def procesar_enlace(update: Update, context: CallbackContext):
    url_propiedad = update.message.text
    user = update.message.from_user
    
    msg_estado = update.message.reply_text("🔍 *Analizando enlace...*", parse_mode='Markdown')

    try:
        # 1. Scraper
        msg_estado.edit_text("⚙️ *Conectando con el servidor local...*")
        res = requests.post(f"{NGROK_URL}/scrape/zonaprop", json={"url": url_propiedad}, timeout=60)
        resultado = res.json()

        if not resultado.get('ok'):
            return msg_estado.edit_text("❌ *Error:* No pudimos obtener los datos.")

        data = resultado['data']
        
        # 2. Definir IDs y Carpetas
        ficha_id = f"prop_{datetime.now().strftime('%H%M%S')}"
        carpeta_local = f"temp_{ficha_id}"
        os.makedirs(carpeta_local, exist_ok=True)

        msg_estado.edit_text("🎨 *Generando diseño de ficha...*")

        # 3. Contacto del Usuario
        contacto_url = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user.id}"

        # 4. Reemplazos en el HTML
        with open('ficha_template.html', 'r', encoding='utf-8') as f:
            template = f.read()

        detalles_str = "".join([f"<li><strong>{k}:</strong> {v}</li>" for k, v in data.get('caracteristicas', {}).items()])

        html_final = template.replace("{{ TITULO }}", data['titulo']) \
                             .replace("{{ PRECIO }}", data['precio']) \
                             .replace("{{ UBICACION }}", data['ubicacion']) \
                             .replace("{{ DESCRIPCION }}", data['descripcion']) \
                             .replace("{{ IMAGEN_URL }}", data['imagenes'][0] if data['imagenes'] else "") \
                             .replace("{{ TELEGRAM_URL }}", contacto_url) \
                             .replace("{{ DETALLES }}", f"<ul>{detalles_str}</ul>") \
                             .replace("{{ FICHA_ID }}", ficha_id) \
                             .replace("{{ AGENCIA }}", "Administración y Gestión")

        with open(os.path.join(carpeta_local, "index.html"), "w", encoding='utf-8') as f:
            f.write(html_final)

        # 5. Subida a GitHub
        msg_estado.edit_text("🚀 *Publicando en la web...*")
        subir_ficha_a_github(ficha_id, carpeta_local)

        # 6. Final
        link_web = f"https://{GITHUB_OWNER.lower()}.github.io/{GITHUB_REPO}/fichas/{ficha_id}/index.html"
        
        texto_final = (
            "✅ *¡Ficha generada!*\n\n"
            f"🏠 *{data['titulo']}*\n"
            f"💰 *{data['precio']}*\n\n"
            f"🌐 [VER FICHA ONLINE]({link_web})"
        )
        msg_estado.edit_text(texto_final, parse_mode='Markdown')

        shutil.rmtree(carpeta_local)

    except Exception as e:
        if 'carpeta_local' in locals() and os.path.exists(carpeta_local):
            shutil.rmtree(carpeta_local)
        msg_estado.edit_text(f"⚠️ *Hubo un problema:* \n`{str(e)}`", parse_mode='Markdown')

# --- CONFIGURACIÓN DEL BOT ---
TOKEN_TELEGRAM = os.getenv("TELEGRAM_TOKEN")
updater = Updater(TOKEN_TELEGRAM)
dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, procesar_enlace))

if __name__ == "__main__":
    updater.start_polling()
    updater.idle()