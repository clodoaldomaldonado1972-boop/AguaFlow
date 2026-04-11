# 1. Usa a imagem slim, mas precisamos instalar pacotes do sistema
FROM python:3.11-slim

# 2. Instala dependências do Sistema (Crucial para OpenCV e Tesseract)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. Copia os arquivos
COPY . .

# 4. Instala as bibliotecas Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "flet>=0.21.0" qrcode Pillow reportlab pytesseract opencv-python supabase python-dotenv

# 5. Expõe a porta
EXPOSE 8080

# 6. Comando de execução
CMD ["python", "main.py"]