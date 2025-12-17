# api.py
from flask import Flask, request, jsonify
from generador_fichas import crear_ficha_con_datos
import logging

app = Flask(__name__)
logger = logging.getLogger(__name__)

@app.route("/generar-ficha", methods=["POST"])
def generar_ficha():
    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON vacío"}), 400

    try:
        ficha_id, carpeta = crear_ficha_con_datos(
            datos=data,
            telegram_url=data.get("telegram_url", ""),
            agencia=data.get("agencia", "SIN AGENCIA")
        )

        return jsonify({
            "ok": True,
            "ficha_id": ficha_id,
            "url": f"https://tierrasapiens.github.io/fichas-prop/fichas/{ficha_id}/"
        })

    except Exception as e:
        logger.exception("Error generando ficha")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)