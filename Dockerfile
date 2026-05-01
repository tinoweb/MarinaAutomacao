FROM python:3.11-slim

# Evita prompts interativos
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala dependencias do sistema para Playwright/Chromium + MySQL client
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    gnupg \
    ca-certificates \
    libnss3 \
    libatk-bridge2.0-0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libgtk-3-0 \
    libxshmfence1 \
    libglu1-mesa \
    libgles2-mesa \
    fonts-liberation \
    libu2f-udev \
    libvulkan1 \
    xdg-utils \
    libdrm2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Instala navegadores do Playwright
RUN playwright install chromium
RUN playwright install-deps chromium

# Copia codigo da aplicacao
COPY . .

# Torna o entrypoint executavel
RUN chmod +x /app/entrypoint.sh

# Porta do Flask
EXPOSE 5000

# Entrypoint aguarda MySQL e inicia a aplicacao
CMD ["/app/entrypoint.sh"]
