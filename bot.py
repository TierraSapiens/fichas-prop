# bot.py
import os
import re
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

# Importa la función crear_ficha desde tu generador mejorado
# Asegurate que el archivo se llame exactamente generador_fichas.py y tenga la función crear_ficha(url_propiedad)
from generador_fichas import crear_ficha

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Falta la variable de entorno TELEGRAM_TOKEN")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# Detecta URLs (simple) y verifica que sea ZonaProp
ZONAPROP_DOMAINS = ["zonaprop.com", "zonaprop.com.ar", "www.zonaprop.com.ar", "www.zonaprop.com"]

def extraer_url_zonaprop(texto: str):
    """
    Busca una URL en el texto y devuelve la primera que contenga 'zonaprop'.
    """
    # regex simple para urls
    urls = re.findall(r"https?://[^\s]+", texto)
    for u in urls:
        if any(domain in u.lower() for domain in ZONAPROP_DOMAINS):
            # limpiar comas o paréntesis finales
            return u.rstrip('),.')
    return None

@dp.message_handler()
async def manejar_mensajes(message: types.Message):
    text = message.text or ""
    url = extraer_url_zonaprop(text)

    if not url:
        # Si el usuario no envía un link válido, sugerimos cómo usarlo
        await message.reply(
            "📎 Envíame el link del aviso de ZonaProp. Ejemplo:\n"
            "https://www.zonaprop.com.ar/..."
        )
        return

    # Aceptó un link de ZonaProp -> comenzamos proceso
    await message.reply("✅ Generando la ficha, por favor espere unos segundos...")

    try:
        # ejecutar la función bloqueante en un thread para no bloquear el loop async
        loop = asyncio.get_event_loop()
        ficha_id, carpeta = await loop.run_in_executor(None, crear_ficha, url)

        # URL pública (ajustala si cambia tu GitHub Pages)
        public_url = f"https://tierrasapiens.github.io/fichas-prop/fichas/{ficha_id}/"

        # 1) Enviar link principal
        await message.reply(f"🔗 Aquí tienes tu ficha:\n{public_url}")

        # 2) Enviar mensaje para reenviar (esto es lo que querés que actúe como propaganda)
        # Enviar como texto simple con link para que Telegram genere la preview (OG meta tags en el HTML)
        await message.reply(f"Encontré esta propiedad que te puede interesar:\n{public_url}")

    except Exception as e:
        # log sencillo y feedback al usuario
        print("Error al generar ficha:", e)
        await message.reply("❌ Ocurrió un error generando la ficha. Reintentá en unos segundos.")

if __name__ == "__main__":
    # Inicia polling (en Railway también puede funcionar si lo ejecutás como worker)
    print("Bot iniciado. Esperando mensajes...")
    executor.start_polling(dp, skip_updates=True)