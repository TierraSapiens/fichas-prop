import os
import json
import random
import string
from datetime import datetime
import subprocess

# ---------------------------------------------------------
# 1. Generar ID aleatorio seguro (20 caracteres)
# ---------------------------------------------------------
def generar_id_unico():
    caracteres = string.ascii_letters + string.digits
    largo = 20

    # cargar IDs ya usados
    if os.path.exists("ids_generados.json"):
        with open("ids_generados.json", "r", encoding="utf-8") as f:
            usados = set(json.load(f))
    else:
        usados = set()

    # generar hasta obtener uno nuevo
    while True:
        nuevo_id = ''.join(random.choice(caracteres) for _ in range(largo))
        if nuevo_id not in usados:
            usados.add(nuevo_id)
            break

    # guardar IDs usados
    with open("ids_generados.json", "w", encoding="utf-8") as f:
        json.dump(list(usados), f, indent=2)

    return nuevo_id


# ---------------------------------------------------------
# 2. Generar HTML de la ficha dentro de su carpeta única
# ---------------------------------------------------------
def crear_ficha():
    ficha_id = generar_id_unico()

    carpeta_ficha = os.path.join("fichas", ficha_id)
    os.makedirs(carpeta_ficha, exist_ok=True)

    ruta_html = os.path.join(carpeta_ficha, "index.html")

    html = f"""
<html>
<head>
<meta charset="utf-8">
<title>Ficha {ficha_id}</title>
</head>
<body>
<h1>Ficha generada</h1>
<p>ID único: <b>{ficha_id}</b></p>
<p>Fecha/Hora de creación:<br> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
<p>URL pública:<br>
https://tierrasapiens.github.io/fichas-prop/{ficha_id}/
</p>
</body>
</html>
"""

    with open(ruta_html, "w", encoding="utf-8") as f:
        f.write(html)

    return ficha_id, carpeta_ficha


# ---------------------------------------------------------
# 3. Commit + push automático a GitHub
# ---------------------------------------------------------
def enviar_a_github(ruta_carpeta, ficha_id):
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", f"Agregar ficha {ficha_id}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("Cambios enviados a GitHub correctamente.")
    except Exception as e:
        print("Error al enviar a GitHub:", e)


# ---------------------------------------------------------
# 4. Ejecutar proceso completo
# ---------------------------------------------------------
if __name__ == "__main__":
    ficha_id, carpeta = crear_ficha()

    print(f"\n--- FICHA GENERADA ---")
    print(f"Carpeta: {carpeta}")
    print(f"ID: {ficha_id}")
    print(f"URL pública:")
    print(f"https://tierrasapiens.github.io/fichas-prop/{ficha_id}/\n")

    enviar_a_github(carpeta, ficha_id)