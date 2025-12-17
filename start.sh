#!/bin/bash

# Este script se ejecuta en Railway para asegurar las dependencias del sistema y Playwright

# 1. Instalar dependencias de Playwright para Linux (lo que evita el error inicial)
echo "Instalando dependencias de Linux..."
apt-get update && apt-get install -y \
    libatk1.0-0 \
    libgtk-3-0 \
    libxss1 \
    libgbm-dev \
    libglib2.0-0 \
    libnss3 \
    libgdk-pixbuf2.0-0 \
    libsecret-1-0 \
    libxcb-dri3-0

# 2. Instalar el navegador Chromium
echo "Instalando Chromium para Playwright..."
playwright install chromium --with-deps

# 3. Iniciar la aplicación Python
echo "Iniciando el bot..."
python bot.py