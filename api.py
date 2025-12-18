# -----------------------------
# api.py V 0.2.txt — Flask Local + Playwright carlo17/12/25
# -----------------------------

from flask import Flask, request, jsonify
import logging

from scrapers.zonaprop import scrapear_zonaprop

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "status": "API activa"})

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)

    app.logger.info("WEBHOOK RECIBIDO DESDE RAILWAY")
    app.logger.info(f"Payload: {data}")

    return jsonify({
        "ok": True,
        "mensaje": "Webhook recibido correctamente"
    })

@app.route("/scrapear", methods=["POST"])
def scrapear_endpoint():
    payload = request.get_json(silent=True)

    if not payload or "url" not in payload:
        return jsonify({"error": "Falta la URL"}), 400

    url = payload["url"]
    app.logger.info(f"Scrapeando URL: {url}")

    datos = scrapear_zonaprop(url)

    return jsonify({
        "ok": True,
        "datos": datos
    })

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )