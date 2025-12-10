#-------------
# Bot.py V 0.1
#--------------
import os
import re
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from generador_fichas import crear_ficha

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

print("DEBUG - Variables de entorno visibles:", list(os.environ.keys()))
print("DEBUG - Valor TELEGRAM_TOKEN:", os.getenv("TELEGRAM_TOKEN"))

if not TELEGRAM_TOKEN:
    raise RuntimeError("Falta la variable de entorno TELEGRAM_TOKEN")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

ZONAPROP_DOMAINS = ["zonaprop.com", "zonaprop.com.ar", "www.zonaprop.com.ar", "www.zonaprop.com"]

def extraer_url_zonaprop(texto: str):
    """
    Busca una URL en el texto y devuelve la primera que contenga 'zonaprop'.
    """
    urls = re.findall(r"https?://[^\s]+", texto)
    for u in urls:
        if any(domain in u.lower() for domain in ZONAPROP_DOMAINS):
            return u.rstrip('),.')
    return None

@dp.message_handler()
async def manejar_mensajes(message: types.Message):
    text = message.text or ""
    url = extraer_url_zonaprop(text)

    if not url:
        await message.reply(
            "📎 Envíame el link del aviso de ZonaProp. Ejemplo:\n"
            "https://www.zonaprop.com.ar/..."
        )
        return

    await message.reply("✅ Generando la ficha, por favor espere unos segundos...")

    try:
        loop = asyncio.get_event_loop()
        ficha_id, carpeta = await loop.run_in_executor(None, crear_ficha, url)

        public_url = f"https://tierrasapiens.github.io/fichas-prop/fichas/{ficha_id}/"

        await message.reply(f"🔗 Aquí tienes tu ficha:\n{public_url}")
        await message.reply(f"Encontré esta propiedad que te puede interesar:\n{public_url}")

    except Exception as e:
        print("Error al generar ficha:", e)
        await message.reply("❌ Ocurrió un error generando la ficha. Reintentá en unos segundos.")

if __name__ == "__main__":
    logging.info("Bot iniciado. Esperando mensajes...")
    executor.start_polling(dp, skip_updates=True)