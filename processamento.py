import cv2
import pytesseract
import numpy as np


def processar_foto_hidrometro(caminho_foto):
    # 1. Carregar a imagem
    img = cv2.imread(caminho_foto)
    if img is None:
        return None, None

    # Redimensionar para facilitar o processamento (Padrão HD)
    largura_alvo = 1280
    fator = largura_alvo / img.shape[1]
    img = cv2.resize(img, (largura_alvo, int(img.shape[0] * fator)))

    # --- ETAPA A: QR CODE (Aprimorado) ---
    detector = cv2.QRCodeDetector()

    # Tentativa 1: Imagem original
    dados_qr, _, _ = detector.detectAndDecode(img)

    # Tentativa 2: Se falhar, forçar contraste (ajuda muito com reflexo)
    if not dados_qr:
        # alpha=2.0 (dobro de contraste), beta=0 (brilho original)
        img_contraste = cv2.convertScaleAbs(img, alpha=2.0, beta=0)
        dados_qr, _, _ = detector.detectAndDecode(img_contraste)

    # --- ETAPA B: OCR (Leitura do Hidrômetro) ---
    cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Suaviza para tirar granulação da câmera do celular
    blur = cv2.GaussianBlur(cinza, (5, 5), 0)

    # Threshold Adaptativo: Ignora sombras do subsolo
    binaria = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 11, 2
    )

    # Configuração Tesseract apenas para números
    config_ocr = '--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789'

    try:
        leitura_texto = pytesseract.image_to_string(binaria, config=config_ocr)
        valor_final = "".join(filter(str.isdigit, leitura_texto))
    except:
        valor_final = ""

    print(f"🔍 AGUA FLOW DEBUG - QR: {dados_qr} | Valor: {valor_final}")

    return dados_qr if dados_qr else None, valor_final if valor_final else None
