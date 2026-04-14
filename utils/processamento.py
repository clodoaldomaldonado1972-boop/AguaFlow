import cv2
import pytesseract
import numpy as np
import os

# Configuração do caminho do Tesseract (Ajuste se necessário)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def processar_foto_hidrometro(caminho_foto, tipo_leitura="AGUA"):
    """
    Processa a imagem para extrair QR Code e leitura numérica.
    tipo_leitura: "AGUA" ou "GAS"
    """
    img = cv2.imread(caminho_foto)
    if img is None:
        return None, None

    # 1. Redimensionamento Padrão (HD)
    largura_alvo = 1280
    fator = largura_alvo / img.shape[1]
    img = cv2.resize(img, (largura_alvo, int(img.shape[0] * fator)))

    # --- ETAPA A: QR CODE ---
    detector = cv2.QRCodeDetector()
    dados_qr, _, _ = detector.detectAndDecode(img)

    # --- ETAPA B: OCR (Pré-processamento) ---
    cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    if tipo_leitura == "GAS":
        # Filtro para medidores de gás (geralmente fundo escuro ou reflexos metálicos)
        final_img = cv2.threshold(cinza, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    else:
        # Filtro para medidores de água (Geralmente plástico e luz direta)
        blur = cv2.medianBlur(cinza, 3)
        final_img = cv2.adaptiveThreshold(
            blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )

    # Dilação para melhorar a leitura de números digitais/segmentados
    kernel = np.ones((2, 2), np.uint8)
    final_img = cv2.dilate(final_img, kernel, iterations=1)

    # Configuração: PSM 7 (Linha única) + Whitelist de números
    config_ocr = '--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789'

    try:
        leitura_texto = pytesseract.image_to_string(final_img, config=config_ocr)
        return dados_qr, leitura_texto.strip()
    except Exception as e:
        print(f"Erro OCR: {e}")
        return dados_qr, None