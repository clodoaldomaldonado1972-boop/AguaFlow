import cv2
import pytesseract
import numpy as np
import time

# --- CHAVE DE CONTROLE INTERNA ---
# Mude para False quando for usar a câmera real no Windows
MODO_SIMULADOR = True


def processar_foto_hidrometro(caminho_foto):
    """
    Processa a foto do hidrômetro. Se o MODO_SIMULADOR estiver ativo,
    ignora a imagem e retorna dados fixos para teste[cite: 14].
    """
    if MODO_SIMULADOR:
        print("--- [SIMULADOR VISION] Ignorando imagem física e gerando dados ---")
        time.sleep(1.2)  # Simula o tempo de processamento do OCR
        return "Apto 101", "00542.30"

    # --- LÓGICA REAL DE PROCESSAMENTO (OpenCV / Tesseract)[cite: 14] ---
    img = cv2.imread(caminho_foto)
    if img is None:
        return None, None

    # Redimensionamento para padrão HD[cite: 14]
    largura_alvo = 1280
    fator = largura_alvo / img.shape[1]
    img = cv2.resize(img, (largura_alvo, int(img.shape[0] * fator)))

    # Detecção de QR Code[cite: 14]
    detector = cv2.QRCodeDetector()
    dados_qr, _, _ = detector.detectAndDecode(img)

    # Pré-processamento OCR[cite: 14]
    cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(cinza, 3)
    binaria = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 11, 2
    )

    # Configuração Tesseract[cite: 14]
    config_ocr = '--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789'

    try:
        leitura_texto = pytesseract.image_to_string(binaria, config=config_ocr)
        valor_final = "".join(filter(str.isdigit, leitura_texto))
    except Exception as e:
        print(f"❌ Erro OCR: {e}")
        valor_final = ""

    return dados_qr if dados_qr else None, valor_final if valor_final else None
