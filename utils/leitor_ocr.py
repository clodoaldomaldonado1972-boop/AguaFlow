import cv2
import numpy as np
import gc
from utils.ocr_engine import extrair_leitura_hidrometro

def ler_qr_code(img):
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(img)
    return str(data).strip() if data else None

def processar_leitura_completa(caminho_foto, modo="AGUA"):
    """
    Lê a imagem, redimensiona para não travar o APK e extrai dados.
    """
    img_raw = cv2.imread(caminho_foto)
    if img_raw is None:
        return {"status": "Erro", "mensagem": "Falha ao carregar imagem"}

    # REDIMENSIONAMENTO PARA APK (Evita Tela Preta)
    largura_max = 800
    fator = largura_max / img_raw.shape[1]
    img = cv2.resize(img_raw, (largura_max, int(img_raw.shape[0] * fator)))
    
    # Limpa a imagem pesada da RAM
    del img_raw
    gc.collect()

    # 1. Tentar QR Code
    unidade = ler_qr_code(img)
    
    # 2. Processar OCR
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Threshold de Otsu para destacar os números
    processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    
    consumo = extrair_leitura_hidrometro(processed, modo)

    # Limpeza final
    del img, gray, processed
    gc.collect()

    return {
        "status": "Sucesso" if (unidade or consumo) else "Falha",
        "unidade": unidade,
        "consumo": consumo
    }