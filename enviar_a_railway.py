import requests
import json

RAILWAY_API = "https://fichas-prop-production.up.railway.app/generar-ficha"

datos_scrapeados = {
    "titulo": "Casa en venta en Mar del Plata",
    "descripcion": "Excelente propiedad de 4 ambientes...",
    "precio": "USD 120.000",
    "ubicacion": "Mar del Plata",
    "detalles": "4 ambientes | 2 baños | Garage",
    "imagenes": [
        "https://upload.wikimedia.org/wikipedia/commons/3/3f/Frontera.jpg"
    ],
    "telegram_url": "https://t.me/PRUEBA_USUARIO",
    "agencia": "AGENCIA PRUEBA"
}

r = requests.post(
    RAILWAY_API,
    json=datos_scrapeados,
    timeout=20
)

print("Status:", r.status_code)
print("Respuesta:")
print(r.text)