#---------------
# bot.py V 1.7 - FINAL (Modo Pasamanos)
#---------------
import os
import requests
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

NGROK_URL = "https://jamey-gamogenetic-incompliantly.ngrok-free.dev"

def start(update: Update, context: CallbackContext): 
    user_name = update.message.from_user.first_name
    texto_bienvenida = (
        f"🏠 *¡Hola, {user_name}! Bienvenid@ a Ficha Prop.*\n\n"
        "Soy tu asistente para generar tus fichas web Premium.\n\n"
        "📌 *¿Cómo empezar?*\n"
        "Simplemente enviame el **link** de Zonaprop."
    )
    update.message.reply_text(texto_bienvenida, parse_mode='Markdown')

def procesar_enlace(update: Update, context: CallbackContext):
    """Manejo conversacional y procesamiento de links"""
    texto_usuario = update.message.text.lower().strip()
    user = update.message.from_user

    # 1. Filtros de conversación básica
    if texto_usuario in ["hola", "buenas", "inicio", "/start"]:
        return start(update, context)
    
    if "ayuda" in texto_usuario:
        return update.message.reply_text("Pega un link de Zonaprop y yo te devuelvo la Ficha Web lista. 🚀")

    if not "zonaprop.com" in texto_usuario:
        return update.message.reply_text("🤔 Eso no parece un link de Zonaprop. Intentá de nuevo.")

    # 2. INICIO DEL PROCESO
    msg_estado = update.message.reply_text("⏳ *Conectando con tu PC para generar la ficha...*", parse_mode='Markdown')

    try:
        # Enviamos el link y el usuario a tu PC
        # Tu PC (app.py) se encarga de TODO: Scrapear, Diseñar y Subir.
        payload = {
            "url": update.message.text,
            "telegram_user": user.username if user.username else user.first_name
        }
        
        # Timeout de 300 segundos (5 minutos) para que no corte si la subida es lenta
        res = requests.post(f"{NGROK_URL}/scrape/zonaprop", json=payload, timeout=300)
        
        resultado = res.json()

        # 3. RESPUESTA
        if resultado.get('ok'):
            # ¡ACÁ ESTABA EL CAMBIO CLAVE!
            # Ya no armamos HTML acá. Recibimos la URL lista desde tu PC.
            link_final = resultado.get('url_web')
            titulo_prop = resultado.get('titulo', 'Propiedad')

            texto_final = (
                f"✅ *¡Ficha Premium Generada!*\n\n"
                f"🏠 *{titulo_prop}*\n"
                f"🔗 [ABRIR FICHA WEB]({link_final})\n\n"
                f"_{link_final}_"
            )
            msg_estado.edit_text(texto_final, parse_mode='Markdown')
        else:
            # Si la PC reportó un error controlado
            error_txt = resultado.get('error', 'Error desconocido')
            msg_estado.edit_text(f"❌ La PC respondió con error: {error_txt}")

    except requests.exceptions.Timeout:
        # Si pasó mucho tiempo pero quizás la PC sigue trabajando
        msg_estado.edit_text("⏱ *El proceso está tardando...*\nTu PC está trabajando. Revisá tu GitHub en unos minutos, seguramente aparezca ahí.")
        
    except Exception as e:
        msg_estado.edit_text(f"💥 *Error de conexión:* No pude hablar con tu PC.\nChequeá que ngrok esté corriendo y la URL sea la correcta.\n\nError: `{str(e)}`", parse_mode='Markdown')

# INICIO DEL BOT
TOKEN_TELEGRAM = os.getenv("TELEGRAM_TOKEN")
updater = Updater(TOKEN_TELEGRAM)
dp = updater.dispatcher
dp.add_handler(CommandHandler("start", start))
dp.add_handler(MessageHandler(Filters.text & ~Filters.command, procesar_enlace))

if __name__ == "__main__":
    updater.start_polling()
    updater.idle()