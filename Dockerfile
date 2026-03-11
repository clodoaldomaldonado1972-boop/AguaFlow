FROM python:3.11-slim

WORKDIR /app

# Copia tudo do ÁguaFlow
COPY . .

# Instala as bibliotecas (usando o pip que já vimos que funciona)
# Forçamos a atualização do Flet para habilitar o componente de Câmera
RUN pip install --no-cache-dir --upgrade "flet>=0.21.0" qrcode Pillow reportlab pytesseract opencv-python

# Expõe a porta para o Windows enxergar
EXPOSE 8080

# COMANDO NOVO: Roda o python direto no main.py
CMD ["python", "main.py"]