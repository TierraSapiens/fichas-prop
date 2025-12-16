#-------------------------
# bot.py V 1.4 - Telegram + comandos
#-------------------------

import os
import json
import logging
import asyncio
import re

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from generador_fichas import crear_ficha
from github_api import subir_ficha_a_github

# Configuracio
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Falta la variable de entorno TELEGRAM_TOKEN")

OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# Archivo donde se guarda la configuración editable (PANEL SUPERIOR IZQ)
CONFIG_FILE = "config.json"

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot y dispatcher
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

# estados simples en memoria: {chat_id: "agencia" | "titulo"}
pending_action = {}

# Helpers de config
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            logger.exception("Error leyendo config.json, se recreará")

# valores por defecto (talvez cambien a futuro)
    cfg = {
        "agencia": "Administración y Gestión Inmobiliaria",
        "titulo": "Ficha de Propiedad",
        "footer": "Ficha generada · Ficha Prop"
    }
    save_config(cfg)
    return cfg

def save_config(cfg: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)

# Cargar config al inicio
config = load_config()

def es_owner(user: types.User) -> bool:
    try:
        return int(user.id) == int(OWNER_ID)
    except Exception:
        return False

def reply_not_authorized(message: types.Message):
    return message.reply("❌ No tenés permiso para usar este comando.")

# Comandos de ADMinistración
@dp.message_handler(commands=["start", "help"])
async def cmd_start(message: types.Message):
    if es_owner(message.from_user):
        txt = (
            "👋 Bienvenido (Owner).\n\n"
            "Comandos disponibles:\n"
            "/setagencia - Cambiar la marca superior (Agencia)\n"
            "/settitulo - Cambiar el título que aparece en las fichas\n"
            "/verconfig - Ver configuración actual\n"
            "/generar <url> - Generar ficha desde URL (ejemplo)\n"
        )
    else:
        txt = "👋 Hola. Envíame el enlace del aviso de la propiedad para generar la ficha."
    await message.reply(txt)

@dp.message_handler(commands=["verconfig"])
async def cmd_verconfig(message: types.Message):
    if not es_owner(message.from_user):
        return await reply_not_authorized(message)
    cfg = load_config()
    txt = (
        f"Configuración actual:\n\n"
        f"Agencia: {cfg.get('agencia')}\n"
        f"Título: {cfg.get('titulo')}\n"
        f"Footer: {cfg.get('footer')}\n"
    )
    await message.reply(txt)

@dp.message_handler(commands=["setagencia"])
async def cmd_setagencia(message: types.Message):
    if not es_owner(message.from_user):
        return await reply_not_authorized(message)
    await message.reply("📝 Escribí ahora el *nombre de la AGENCIA* que querés mostrar (envialo en un solo mensaje).", parse_mode="Markdown")
    pending_action[message.chat.id] = "agencia"

@dp.message_handler(commands=["settitulo"])
async def cmd_settitulo(message: types.Message):
    if not es_owner(message.from_user):
        return await reply_not_authorized(message)
    await message.reply("📝 Escribí ahora el *TÍTULO* que querés mostrar en las fichas (envialo en un solo mensaje).", parse_mode="Markdown")
    pending_action[message.chat.id] = "titulo"

# Comando Rápido para generar ficha desde Telegram (EN PRUEBA¿?)
@dp.message_handler(commands=["generar"])
async def cmd_generar(message: types.Message):
    if not es_owner(message.from_user):

#Permite que cualquier usuario pida generar ficha si ya tienés ese flujo, o podérlo restringir
        await message.reply("Solo el owner puede usar /generar en este modo. Envíame un enlace para generar desde el bot principal.")
        return

    args = message.get_args().strip()
    if not args:
        await message.reply("Usar:\n/generar https://... (URL del aviso)")
        return
    user = message.from_user
    if user.username:
        telegram_url = f"https://t.me/{user.username}"
    else:
        telegram_url = f"https://t.me/user?id={user.id}"

    url = args.split()[0]
    
    await message.reply("✅ Generando ficha, esto puede tardar unos segundos...")
    loop = asyncio.get_event_loop()
    try:
        ficha_id, carpeta = await loop.run_in_executor(
    None,
    crear_ficha,
    url,
    telegram_url,
    config.get("agencia")
)

# Subir a GitHub (intenta, pero no bloquea al usuario si falla)
        try:
            subir_ficha_a_github(ficha_id, carpeta)
        except Exception as e:
            logger.exception("Error subiendo a GitHub")
        public_url = f"https://tierrasapiens.github.io/fichas-prop/fichas/{ficha_id}/"
        await message.reply(f"🔗 Ficha generada:\n{public_url}")
    except Exception as e:
        logger.exception("Error generando ficha")
        await message.reply("❌ Error generando la ficha. Revisá logs.")

# Handler para mensajes cuando estamos "esperando" entrada del owner
@dp.message_handler()
async def handle_all_messages(message: types.Message):
    chat_id = message.chat.id
# Datos del usuario (Telegram)
    user = message.from_user
    username = user.username          # puede ser None
    user_id = user.id
    nombre = user.first_name or "Usuario"

    if username:
        telegram_url = f"https://t.me/{username}"
    else:
        telegram_url = f"https://t.me/user?id={user_id}"

    if chat_id in pending_action and es_owner(message.from_user):
        action = pending_action.pop(chat_id)
        text = message.text.strip()
        cfg = load_config()

        if action == "agencia":
            cfg["agencia"] = text
            save_config(cfg)
            await message.reply(f"✔️ Agencia actualizada a:\n*{text}*", parse_mode="Markdown")
            return

        if action == "titulo":
            cfg["titulo"] = text
            save_config(cfg)
            await message.reply(f"✔️ Título actualizado a:\n*{text}*", parse_mode="Markdown")
            return

    texto = message.text or ""
    
    urls = re.findall(r"https?://[^\s]+", texto)
    url = None
    if urls:
        url = urls[0]
    if url:
        await message.reply("✅ Generando la ficha, por favor espere unos segundos...")
        loop = asyncio.get_event_loop()
        try:
            ficha_id, carpeta = await loop.run_in_executor(
    None,
    crear_ficha,
    url,
    telegram_url,
    config.get("agencia")
)

# Subir a GitHub automáticamente
            try:
                subir_ficha_a_github(ficha_id, carpeta)
            except Exception as e:
                logger.exception("Error subiendo a GitHub")

# Esperar un poco para que GitHub Pages regenere
            await asyncio.sleep(25)      #<<<< Elejir tiempo espera.!!
            public_url = f"https://tierrasapiens.github.io/fichas-prop/fichas/{ficha_id}/"
            await message.reply(f"🔗 Aquí tienes tu ficha:\n{public_url}")
        except Exception as e:
            logger.exception("Error generando ficha")
            await message.reply("❌ Ocurrió un error generando la ficha. Reintentá en unos segundos.")
        return

# Mensaje por defecto si no es URL ni modo pendiente
    if es_owner(message.from_user):
        await message.reply("⚠️ No entendí. Usá /setagencia o /settitulo para cambiar valores, o envíame el enlace de la propiedad.")
    else:
        await message.reply("👋 Envíame el enlace completo de una ficha (debe contener un aviso inmobiliario).")

# Startup / Shutdown
async def on_startup(dp):
    logger.info("Bot iniciado (aiogram). Owner ID = %s", OWNER_ID)

async def on_shutdown(dp):
    logger.info("Bot apagándose...")

if __name__ == "__main__":
    
# Se puede forzar OWNER_ID desde un archivo local (opcional)
    if OWNER_ID == 0:
        logger.warning("OWNER_ID no configurado. Solo el owner podrá usar comandos si se establece OWNER_ID en las env vars.")
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)