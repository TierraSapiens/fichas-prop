const { Telegraf } = require("telegraf");
const fs = require("fs");
const BOT_TOKEN = "8316220346:AAGdb99O9Q1-9zzPgR2wtN9Lh3bobeCFTKQ";

// Número del dueño autorizado
const OWNER_ID = 1659113101

// Cargar DB
function loadData() {
  if (!fs.existsSync("data.json")) {
    fs.writeFileSync("data.json", JSON.stringify({ agencia: "" }, null, 2));
  }
  return JSON.parse(fs.readFileSync("data.json"));
}

function saveData(data) {
  fs.writeFileSync("data.json", JSON.stringify(data, null, 2));
}

const bot = new Telegraf(BOT_TOKEN);

// El dueño toca el comando /settitulo
bot.command("settitulo", (ctx) => {
  if (ctx.from.id !== OWNER_ID)
    return ctx.reply("❌ No estás autorizado para cambiar el título.");

  ctx.reply("📝 Por favor escribí el *título que querés mostrar* en tu página.\n\nEjemplos:\n• Propiedades García\n• MDQ Inmuebles\n• Faro Propiedades", { parse_mode: "Markdown" });

  // Activar modo “esperando título”
  ctx.session = ctx.session || {};
  ctx.session.waitingTitle = true;
});

// Captura de texto
bot.on("text", (ctx) => {
  if (!ctx.session) ctx.session = {};

  // Sólo si estaba esperando el título
  if (ctx.session.waitingTitle && ctx.from.id === OWNER_ID) {
    const title = ctx.message.text.trim();
    const data = loadData();

    data.agencia = title;
    saveData(data);

    ctx.reply(`✅ Título actualizado.\nTu página mostrará: *"${title}"*`, {
      parse_mode: "Markdown"
    });

    ctx.session.waitingTitle = false;
  }
});

bot.launch();
console.log("Bot iniciado.");