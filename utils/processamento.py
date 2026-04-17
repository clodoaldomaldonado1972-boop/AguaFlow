import cv2
import numpy as np

def processar_foto_hidrometro(caminho_foto, tipo_leitura="AGUA"):
    img = cv2.imread(caminho_foto)
    if img is None: return None, None

    # Redimensiona para HD para manter proporção da mira
    largura_alvo = 1280
    fator = largura_alvo / img.shape[1]
    img = cv2.resize(img, (largura_alvo, int(img.shape[0] * fator)))

    # Melhora o contraste especificamente na linha horizontal central (onde está a mira)
    cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Filtro adaptativo para destacar os números pretos no fundo branco/metal
    blur = cv2.medianBlur(cinza, 3)
    processada = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 11, 2
    )

    # Detecção de QR Code
    detector = cv2.QRCodeDetector()
    dados_qr, _, _ = detector.detectAndDecode(img)

    return dados_qr, processada