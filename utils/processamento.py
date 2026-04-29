import cv2
import numpy as np
import gc  # Garbage Collector para libertar RAM imediatamente
from utils.ocr_engine import extrair_leitura_hidrometro

def processar_foto_hidrometro(caminho_foto, modo="AGUA"):
    """
    Processa a foto para extrair Unidade (QR) e Consumo (OCR).
    Aplica redução de resolução para evitar 'Tela Preta' no Android.
    """
    # 1. Carregamento da Imagem
    img_raw = cv2.imread(caminho_foto)
    if img_raw is None: 
        return None, None

    # 2. REDIMENSIONAMENTO AGRESSIVO (Segurança para APK)
    # Reduzimos para 1080px de largura para economizar memória sem perder precisão
    largura_alvo = 1080
    fator = largura_alvo / img_raw.shape[1]
    img = cv2.resize(img_raw, (largura_alvo, int(img_raw.shape[0] * fator)))

    # Libertar a foto original da memória imediatamente
    del img_raw
    gc.collect()

    # 3. Tratamento para OCR
    cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Filtro de Nitidez para o Gás (os dígitos costumam ser menores)
    if modo == "GAS":
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        cinza = cv2.filter2D(cinza, -1, kernel)

    blur = cv2.medianBlur(cinza, 3)
    
    # Threshold Adaptativo: Ideal para lidar com a lanterna do telemóvel no shaft
    processada = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 11, 2
    )

    # 4. Detecção de Unidade (QR Code)
    detector = cv2.QRCodeDetector()
    unidade, _, _ = detector.detectAndDecode(img)

    # 5. Extração de Consumo (OCR)
    # Passamos o modo para validar se são 2 ou 3 decimais
    consumo = extrair_leitura_hidrometro(processada, modo=modo)

    # Limpeza de memória antes de retornar
    del cinza, blur, processada, img
    gc.collect()

    return unidade, consumo