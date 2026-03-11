import cv2
import pytesseract
import numpy as np


def processar_foto_hidrometro(caminho_foto):
    """
    MODULO DE PROCESSAMENTO DE IMAGEM
    Recebe o caminho da foto tirada pelo celular e tenta extrair o QR Code e o valor.
    """
    # 1. Carrega a imagem capturada
    img = cv2.imread(caminho_foto)
    if img is None:
        return None, None

    # --- ETAPA A: IDENTIFICAÇÃO DO APARTAMENTO (QR CODE) ---
    detector = cv2.QRCodeDetector()
    dados_qr, _, _ = detector.detectAndDecode(img)

    # --- ETAPA B: LEITURA DOS NÚMEROS (OCR) ---
    # Convertemos para escala de cinza e aplicamos um filtro (Otsu) para destacar os números
    # Isso ajuda na precisão dentro dos subsolos do Vivere Prudente
    cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binaria = cv2.threshold(
        cinza, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    # Configuramos o Tesseract para ler apenas dígitos (0-9)
    config_ocr = '--psm 7 -c tessedit_char_whitelist=0123456789'
    leitura_texto = pytesseract.image_to_string(binaria, config=config_ocr)

    # Retorna o que encontrou (QR Code e o valor numérico)
    return dados_qr, leitura_texto.strip()
