#-------------
# Bot.py V 0.1
#--------------
import os
import re
import asyncio
import logging

# Mensajes personalizables
MSG_INTRO = "¡Hola! 👋 Soy el bot de Ficha Prop MDQ. Envíame el link del aviso y te genero una ficha"
MSG_NO_URL = (
    "📎 Envíame el link del aviso de ZonaProp. Ejemplo:\n"
    "https://www.zonaprop.com.ar/..."
)
MSG_GENERANDO = "✅ Generando la ficha, por favor espera unos segundos..."
MSG_FICHA_PUBLIC = "🔗 Aquí tienes tu ficha:\n{public_url}"
MSG_FICHA_SUG = "Encontré esta propiedad que te puede interesar:\n{public_url}"
MSG_ERROR = "❌ Ocurrió un error generando la ficha. Reintentá en unos segundos."

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from generador_fichas import crear_ficha

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    raise RuntimeError("Falta la variable de entorno TELEGRAM_TOKEN")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

ZONAPROP_DOMAINS = ["zonaprop.com", "zonaprop.com.ar", "www.zonaprop.com.ar", "www.zonaprop.com"]

def extraer_url_zonaprop(texto: str):
    urls = re.findall(r"https?://[^\s]+", texto)
    for u in urls:
        if any(domain in u.lower() for domain in ZONAPROP_DOMAINS):
            return u.rstrip('),.')
    return None

@dp.message_handler()
async def manejar_mensajes(message: types.Message):
    text = message.text or ""
    url = extraer_url_zonaprop(text)

# Nombre del usuario para el saludo
    nombre = message.from_user.first_name or ""

# Si NO envió URL → enviar saludo + pedir link
    if not url:
        await message.reply(
            f"Hola {nombre}\n"
            "📎 Envíame el link del aviso de ZonaProp. Ejemplo:\n"
            "https://www.zonaprop.com.ar/..."
        )
        return

# SÍ hay URL → generar la ficha
    await message.reply("✅ Generando la ficha, por favor espere unos segundos...")

    try:
        public_url = await crear_ficha(url)
        await message.reply(f"🔗 Aquí tienes tu ficha:\n{public_url}")
        await message.reply(f"También te puede interesar esta otra:\n{public_url}")

    except Exception as e:
        logging.error(f"Error generando ficha: {e}")
        await message.reply("❌ Ocurrió un error generando la ficha. Reintentá en unos segundos.")

    try:
        loop = asyncio.get_event_loop()
        ficha_id, carpeta = await loop.run_in_executor(None, crear_ficha, url)

        public_url = f"https://tierrasapiens.github.io/fichas-prop/fichas/{ficha_id}/"

        await message.reply(MSG_FICHA_PUBLIC.format(public_url=public_url))
        await message.reply(MSG_FICHA_SUG.format(public_url=public_url))

    except Exception as e:
        print("Error al generar ficha:", e)
        await message.reply(MSG_ERROR)

if __name__ == "__main__":
    logging.info("Bot iniciado. Esperando mensajes...")
    executor.start_polling(dp, skip_updates=True)