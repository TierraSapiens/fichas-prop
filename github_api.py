import base64
import requests
import os

# 🔧 Configuración de GitHub
GITHUB_OWNER = "TierraSapiens"         # <-- Tu usuario EXACTO
GITHUB_REPO = "fichas-prop"            # <-- Tu repositorio
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # <-- token API desde Railway

if not GITHUB_TOKEN:
    raise RuntimeError("❌ Falta la variable de entorno GITHUB_TOKEN")

API_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents"


def upload_file(path_repo, local_file_path, message):
    """
    Sube un archivo a GitHub usando la API REST v3.
    path_repo: ruta dentro del repo (ej: 'fichas/abc123/index.html')
    local_file_path: ruta local al archivo
    """

    # Leer archivo local
    with open(local_file_path, "rb") as f:
        content = f.read()

    encoded = base64.b64encode(content).decode("utf-8")

    url = f"{API_URL}/{path_repo}"

    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    # Primero revisamos si ya existe el archivo en GitHub (para obtener SHA)
    resp = requests.get(url, headers=headers)

    if resp.status_code == 200:
        sha = resp.json()["sha"]
    else:
        sha = None  # archivo nuevo

    data = {
        "message": message,
        "content": encoded,
    }

    if sha:
        data["sha"] = sha

    # Subir archivo
    put_resp = requests.put(url, headers=headers, json=data)

    if put_resp.status_code in (200, 201):
        return True
    else:
        raise RuntimeError(
            f"Error subiendo archivo a GitHub: {put_resp.status_code}\n{put_resp.text}"
        )


def subir_ficha_a_github(ficha_id, carpeta_local):
    """
    Sube la carpeta generada de una ficha:
    fichas/<ID>/index.html
    """
    repo_path = f"fichas/{ficha_id}/index.html"
    local_path = f"{carpeta_local}/index.html"

    mensaje = f"Agregar ficha {ficha_id}"

    return upload_file(repo_path, local_path, mensaje)