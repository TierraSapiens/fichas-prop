#---------------------
# Bot.py V 1.2
#--------------------
import os
import re
import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

from github_api import subir_ficha_a_github
from generador_fichas import crear_ficha

logging.basicConfig(level=logging.INFO)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    raise RuntimeError("Falta la variable de entorno TELEGRAM_TOKEN")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

DOMINIOS_PERMITIDOS = [
    "zonaprop.com", "zonaprop.com.ar",
    "www.zonaprop.com", "www.zonaprop.com.ar",
    "argenprop.com", "www.argenprop.com",
    "inmuebles.clarin.com", "www.inmuebles.clarin.com",
    "properati.com.ar", "www.properati.com.ar",
    "inmuebles.mercadolibre.com.ar", "www.inmuebles.mercadolibre.com.ar",
    "soloduenos.com", "www.soloduenos.com"
]

def extraer_url(texto: str):
    urls = re.findall(r"https?://[^\s]+", texto)
    for u in urls:
        if any(domain in u.lower() for domain in DOMINIOS_PERMITIDOS):
            return u.rstrip('),.')
    return None

@dp.message_handler()
async def manejar_mensajes(message: types.Message):
    text = message.text or ""
    url = extraer_url(text)
    nombre = message.from_user.first_name or ""

    if not url:
        await message.reply(
            f"Hola {nombre}\n"
            "📎 Envíame el link del aviso de la propiedad:"
        )
        return

    await message.reply("✅ Generando la ficha, por favor espere unos segundos...")

    try:
        loop = asyncio.get_event_loop()
        ficha_id, carpeta = await loop.run_in_executor(None, crear_ficha, url)

#Subir a GitHub automáticamente
        try:
            subir_ficha_a_github(ficha_id, carpeta)
        except Exception as e:
            logging.error(f"Error subiendo a GitHub: {e}")

        await asyncio.sleep(10) #Esperar unos segundos para la propagación de GitHub Pages

        public_url = f"https://tierrasapiens.github.io/fichas-prop/fichas/{ficha_id}/"
        await message.reply(f"🔗 Aquí tienes tu ficha:\n{public_url}")

    except Exception as e:
        logging.error(f"Error generando ficha: {e}")
        await message.reply("❌ Ocurrió un error generando la ficha. Reintentá en unos segundos.")

if __name__ == "__main__":
    logging.info("Bot iniciado. Esperando mensajes...")
    executor.start_polling(dp, skip_updates=True)