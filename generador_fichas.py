import os
import subprocess
from datetime import datetime

# Carpeta donde se guardarán las fichas HTML
OUTPUT_DIR = "fichas"

def generar_ficha_dummy():
    """Genera una ficha simple para probar Railway + GitHub Pages."""
    ahora = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"ficha_{ahora}.html"
    ruta = os.path.join(OUTPUT_DIR, nombre_archivo)

    contenido = f"""
    <html>
    <head><meta charset="utf-8"><title>Ficha {ahora}</title></head>
    <body>
        <h1>Ficha generada automáticamente</h1>
        <p>Hora de creación: {ahora}</p>
    </body>
    </html>
    """

    with open(ruta, "w", encoding="utf-8") as f:
        f.write(contenido)

    print(f"Ficha generada: {ruta}")
    return nombre_archivo


def git_push(mensaje="Agregar nueva ficha"):
    """Hace commit y push automático al repo."""
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", mensaje], check=True)
    subprocess.run(["git", "push"], check=True)
    print("Cambios enviados a GitHub")


if __name__ == "__main__":
    nombre = generar_ficha_dummy()
    git_push(f"Generar ficha {nombre}")