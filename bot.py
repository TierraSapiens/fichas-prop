#---------------
# bot.py V 1.5 - Garbo 20/12/2025
#---------------
import os
import requests
import shutil
from datetime import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from github_api import subir_ficha_a_github

# Configuracion
NGROK_URL = "https://jamey-gamogenetic-incompliantly.ngrok-free.dev"
GITHUB_OWNER = "TierraSapiens"
GITHUB_REPO = "fichas-prop"

def start(update: Update, context: CallbackContext): 
    """Diálogo de bienvenida (Formato de arranque)"""
    user_name = update.message.from_user.first_name
    texto_bienvenida = (
        f"🏠 *¡Hola, {user_name}! Bienvenid@ a Ficha Prop.*\n\n"
        "Soy tu asistente para generar tus fichas web.\n\n"
        "📌 *¿Cómo empezar?*\n"
        "Simplemente enviame el **link** de la propiedad que te interese."
    )
    update.message.reply_text(texto_bienvenida, parse_mode='Markdown')

def procesar_enlace(update: Update, context: CallbackContext):
    """Manejo conversacional y procesamiento de links"""
    texto_usuario = update.message.text.lower().strip()
    user = update.message.from_user

    # 1. Saludos
    if texto_usuario in ["hola", "buenas", "buen día", "buen dia", "hola!", "inicio"]:
        return start(update, context)

    # 2. Agradecimientos
    if texto_usuario in ["gracias", "gracias!", "gracias !", "muchas gracias", "joya", "buenísimo", "buenisimo"]:
        return update.message.reply_text(f"¡De nada, {user.first_name}! Quedo a la espera de tu próximo link. 😊")

    # 3. Ayuda
    if "ayuda" in texto_usuario or "como funciona" in texto_usuario:
        return update.message.reply_text(
            "📖 *Guía rápida:*\n\n"
            "1. Buscá una propiedad.\n"
            "2. Copiá el link de la barra de direcciones.\n"
            "3. Pegalo acá y yo me encargo del resto.\n\n"
            "¿Tenés algún link para probar?", 
            parse_mode='Markdown'
        )

    # 4. Si no es saludo ni ayuda, verifica si es un link
    if not texto_usuario.startswith("http"):
        return update.message.reply_text(
            "🤔 No entendí este mensaje. Si querés una ficha, enviame un **link de Zonaprop**.\n"
            "Si necesitás ayuda, escribí 'ayuda'.",
            parse_mode='Markdown'
        )

    # SI pasa todas la validaciones, es un link empieza scraping
    url_recibida = update.message.text
    msg_estado = update.message.reply_text("🔍 *Analizando propiedad...*", parse_mode='Markdown')

    try:
        # 1. Llamada al Scraper en PC
        msg_estado.edit_text("⚙️ *Conectando con el servidor local...*\n(Extrayendo datos ⏳)")
        res = requests.post(f"{NGROK_URL}/scrape/zonaprop", json={"url": url_recibida}, timeout=120)
        resultado = res.json()

        if not resultado.get('ok') or resultado['data']['titulo'] == "No encontrado":
            return msg_estado.edit_text("❌ *Error:* No pudimos encontrar datos en ese link. Verificá que sea de Zonaprop.")

        data = resultado['data']
        
        # 2. Preparar ID y Carpetas
        ficha_id = f"prop_{datetime.now().strftime('%H%M%S')}"
        carpeta_local = f"temp_{ficha_id}"
        os.makedirs(carpeta_local, exist_ok=True)

        msg_estado.edit_text("🎨 *Diseñando ficha web personalizada...*")

        # 3. Datos del usuario para el botón de contacto de Telegram
        contacto_url = f"https://t.me/{user.username}" if user.username else f"tg://user?id={user.id}"

        # 4. Generar HTML desde el template
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

        # Guardar archivo temporal
        with open(os.path.join(carpeta_local, "index.html"), "w", encoding='utf-8') as f:
            f.write(html_final)

        # 5. Subida a GitHub
        msg_estado.edit_text("🚀 *Publicando en GitHub Pages...*")
        subir_ficha_a_github(ficha_id, carpeta_local)

        # 6. Entrega del Link Final
        link_web = f"https://{GITHUB_OWNER.lower()}.github.io/{GITHUB_REPO}/fichas/{ficha_id}/"
        
        texto_final = (
            "✅ *¡Ficha generada con éxito!*\n\n"
            f"🏠 *{data['titulo']}*\n"
            f"💰 *Precio:* {data['precio']}\n\n"
            f"🌐 [VER FICHA AQUÍ]({link_web})"
        )
        msg_estado.edit_text(texto_final, parse_mode='Markdown')

        # Limpiar carpeta temporal
        shutil.rmtree(carpeta_local)

    except Exception as e:
        if 'carpeta_local' in locals() and os.path.exists(carpeta_local):
            shutil.rmtree(carpeta_local)
        msg_estado.edit_text(f"⚠️ *Hubo un problema:* \n`{str(e)}`", parse_mode='Markdown')

# INICIO
TOKEN_TELEGRAM = os.getenv("TELEGRAM_TOKEN")
updater = Updater(TOKEN_TELEGRAM)
dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, procesar_enlace))

if __name__ == "__main__":
    updater.start_polling()
    updater.idle()