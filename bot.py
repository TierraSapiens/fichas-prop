# -------------------------
# bot.py – Telegram Bot (aiogram v2)
# -------------------------

import os
import json
import logging
import asyncio
import re

from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

from generador_fichas import crear_ficha
from github_api import subir_ficha_a_github

# =========================
# CONFIGURACIÓN
# =========================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Falta la variable de entorno TELEGRAM_TOKEN")

OWNER_ID = int(os.getenv("OWNER_ID", "0"))
CONFIG_FILE = "config.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot)

pending_action = {}

# =========================
# CONFIG MANAGER
# =========================

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            logger.exception("Error leyendo config.json, se recreará")

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

config = load_config()

# =========================
# HELPERS
# =========================

def es_owner(user: types.User) -> bool:
    try:
        return int(user.id) == OWNER_ID
    except Exception:
        return False

async def reply_not_authorized(message: types.Message):
    await message.reply("❌ No tenés permiso para usar este comando.")

def get_telegram_url(user: types.User) -> str:
    if user.username:
        return f"https://t.me/{user.username}"
    return f"https://t.me/user?id={user.id}"

# =========================
# COMANDOS
# =========================

@dp.message_handler(commands=["start", "help"])
async def cmd_start(message: types.Message):
    if es_owner(message.from_user):
        txt = (
            "👋 Bienvenido (Owner)\n\n"
            "/setagencia – Cambiar agencia\n"
            "/settitulo – Cambiar título\n"
            "/verconfig – Ver configuración\n"
            "/generar <url> – Generar ficha\n"
        )
    else:
        txt = "👋 Enviame el enlace del aviso para generar la ficha."
    await message.reply(txt)

@dp.message_handler(commands=["verconfig"])
async def cmd_verconfig(message: types.Message):
    if not es_owner(message.from_user):
        return await reply_not_authorized(message)

    cfg = load_config()
    await message.reply(
        f"Agencia: {cfg['agencia']}\n"
        f"Título: {cfg['titulo']}\n"
        f"Footer: {cfg['footer']}"
    )

@dp.message_handler(commands=["setagencia"])
async def cmd_setagencia(message: types.Message):
    if not es_owner(message.from_user):
        return await reply_not_authorized(message)

    pending_action[message.chat.id] = "agencia"
    await message.reply("📝 Escribí el nombre de la agencia")

@dp.message_handler(commands=["settitulo"])
async def cmd_settitulo(message: types.Message):
    if not es_owner(message.from_user):
        return await reply_not_authorized(message)

    pending_action[message.chat.id] = "titulo"
    await message.reply("📝 Escribí el título")

@dp.message_handler(commands=["generar"])
async def cmd_generar(message: types.Message):
    if not es_owner(message.from_user):
        return await reply_not_authorized(message)

    args = message.get_args().strip()
    if not args:
        return await message.reply("Uso: /generar <url>")

    url = args.split()[0]
    await generar_ficha(message, url)

# =========================
# HANDLER GENERAL
# =========================

@dp.message_handler()
async def handle_all_messages(message: types.Message):
    chat_id = message.chat.id

    # Acciones pendientes (setagencia / settitulo)
    if chat_id in pending_action and es_owner(message.from_user):
        action = pending_action.pop(chat_id)
        cfg = load_config()

        if action == "agencia":
            cfg["agencia"] = message.text.strip()
        elif action == "titulo":
            cfg["titulo"] = message.text.strip()

        save_config(cfg)
        return await message.reply("✅ Configuración actualizada")

    # Buscar URL en el mensaje
    texto = message.text or ""
    urls = re.findall(r"https?://[^\s]+", texto)

    if urls:
        await generar_ficha(message, urls[0])
        return

    # Mensaje por defecto
    if es_owner(message.from_user):
        await message.reply("⚠️ Comando no reconocido.")
    else:
        await message.reply("👋 Enviame un enlace válido de una propiedad.")

# =========================
# GENERADOR CENTRAL
# =========================

async def generar_ficha(message: types.Message, url: str):
    telegram_url = get_telegram_url(message.from_user)
    cfg = load_config()

    await message.reply("⏳ Generando ficha, por favor esperá...")

    loop = asyncio.get_event_loop()

    try:
        ficha_id, carpeta = await loop.run_in_executor(
            None,
            crear_ficha,
            url,
            telegram_url,
            cfg["agencia"]
        )

        try:
            subir_ficha_a_github(ficha_id, carpeta)
        except Exception:
            logger.exception("Error subiendo a GitHub")

        await asyncio.sleep(15)

        public_url = f"https://tierrasapiens.github.io/fichas-prop/fichas/{ficha_id}/"
        await message.reply(f"🔗 Ficha generada:\n{public_url}")

    except Exception:
        logger.exception("Error generando ficha")
        await message.reply("❌ Error generando la ficha")

# =========================
# STARTUP / SHUTDOWN
# =========================

async def on_startup(dp):
    logger.info("🤖 Bot iniciado")

async def on_shutdown(dp):
    logger.info("🛑 Bot apagándose")

if __name__ == "__main__":
    if OWNER_ID == 0:
        logger.warning("OWNER_ID no configurado")

    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown
    )