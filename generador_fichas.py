# ------------------------------------------------------------
# generador_fichas.py V 1.5.txt
# ------------------------------------------------------------
import os
from datetime import datetime

def generar_html_ficha(data, usuario_info, template_path='ficha_template.html'):
    # Leer el template
    with open(template_path, 'r', encoding='utf-8') as f:
        html = f.read()

    # Formatear detalles (Características) para el HTML
    detalles_html = "<ul>"
    for k, v in data.get('caracteristicas', {}).items():
        detalles_html += f"<li><strong>{k}:</strong> {v}</li>"
    detalles_html += "</ul>"

    # Preparar los reemplazos
    reemplazos = {
        "{{ TITULO }}": data.get('titulo', 'Propiedad'),
        "{{ DESCRIPCION }}": data.get('descripcion', '').replace('\n', '<br>'),
        "{{ IMAGEN_URL }}": data.get('imagenes', [''])[0], # Primera foto
        "{{ UBICACION }}": data.get('ubicacion', 'Consultar ubicación'),
        "{{ PRECIO }}": data.get('precio', 'Consultar'),
        "{{ PRECIO_SUB }}": "Expensas: Consultar", # Podés extraerlo luego si querés
        "{{ DETALLES }}": detalles_html,
        "{{ FICHA_ID }}": datetime.now().strftime("%Y%m%d%H%M"),
        "{{ FECHA }}": datetime.now().strftime("%d/%m/%Y"),
        "{{ AGENCIA }}": "Propio Inmobiliaria",
        "{{ TELEGRAM_URL }}": f"https://t.me/{usuario_info['username']}" if usuario_info.get('username') else f"tg://user?id={usuario_info['id']}"
    }

    # Reemplazar todo en el HTML
    for tag, valor in reemplazos.items():
        html = html.replace(tag, str(valor))

    return html
