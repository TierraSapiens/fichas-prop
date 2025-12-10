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

    import os

def guardar_ficha_html(titulo, descripcion, nombre_archivo):
    """
    Crea un archivo HTML en /fichas/ con la ficha formateada.
    """
    carpeta = "fichas"

    # Crear carpeta si no existe
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)

    ruta_archivo = os.path.join(carpeta, nombre_archivo)

    html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>{titulo}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 40px;
                line-height: 1.6;
            }}
            .contenedor {{
                border: 1px solid #ccc;
                padding: 20px;
                border-radius: 10px;
                max-width: 800px;
            }}
            h1 {{
                color: #2c3e50;
            }}
        </style>
    </head>

    <body>
        <div class="contenedor">
            <h1>{titulo}</h1>
            <p>{descripcion}</p>
            <hr>
            <p><b>Contacto:</b> +54 9 2235 38-5001</p>
        </div>
    </body>
    </html>
    """

    with open(ruta_archivo, "w", encoding="utf-8") as f:
        f.write(html)

    return ruta_archivo