# bot.py - Versión Integrada
import os
import requests
import shutil
from datetime import datetime
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Importamos la función de tu github_api.py V 0.4
from github_api import subir_ficha_a_github

# Configuración
NGROK_URL = "https://jamey-gamogenetic-incompliantly.ngrok-free.dev"
GITHUB_OWNER = "TierraSapiens"
GITHUB_REPO = "fichas-prop"

def start(update: Update, context: CallbackContext):
    """Diálogo de bienvenida (Formato de arranque)"""
    user_name = update.message.from_user.first_name
    texto_bienvenida = (
        f"🏠 *¡Hola, {user_name}! Bienvenid@ a Ficha Prop.*\n\n"
        "Soy tu asistente para generar fichas web profesionales.\n\n"
        "📌 *¿Cómo empezar?*\n"
        "Simplemente enviame el **link de Zonaprop** de la propiedad que te interese."
    )
    update.message.reply_text(texto_bienvenida, parse_mode='Markdown')

def procesar_enlace(update: Update, context: CallbackContext):
    """Manejo de los mensajes y creación de la ficha"""
    url_recibida = update.message.text
    user = update.message.from_user
    
    # --- VALIDACIÓN DE DIÁLOGO ---
    if not url_recibida.startswith("http"):
        return update.message.reply_text("🤔 *Hola, este no parece un link válido.*\nPor favor, enviame un enlace valido que empiece con `https://...`", parse_mode='Markdown')

    msg_estado = update.message.reply_text("🔍 *Analizando propiedad...*", parse_mode='Markdown')

    try:
        # 1. Llamada al Scraper en tu PC
        msg_estado.edit_text("⚙️ *Conectando con el servidor local...*\n(Extrayendo datos ⏳)")
        res = requests.post(f"{NGROK_URL}/scrape/zonaprop", json={"url": url_recibida}, timeout=70)
        resultado = res.json()

        if not resultado.get('ok') or resultado['data']['titulo'] == "No encontrado":
            return msg_estado.edit_text("❌ *Error:* No pudimos encontrar datos en ese link. Verificá que sea de Zonaprop.")

        data = resultado['data']
        
        # 2. Preparar ID y Carpetas
        ficha_id = f"prop_{datetime.now().strftime('%H%M%S')}"
        carpeta_local = f"temp_{ficha_id}"
        os.makedirs(carpeta_local, exist_ok=True)

        msg_estado.edit_text("🎨 *Diseñando ficha web personalizada...*")

        # 3. Datos del usuario para el botón de contacto
        # Esto cumple tu pedido: Sale con tu contacto/teléfono de Telegram
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

# --- INICIO ---
TOKEN_TELEGRAM = os.getenv("TELEGRAM_TOKEN")
updater = Updater(TOKEN_TELEGRAM)
dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, procesar_enlace))

if __name__ == "__main__":
    updater.start_polling()
    updater.idle()