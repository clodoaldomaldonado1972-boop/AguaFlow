import cv2
import easyocr
import re

reader = easyocr.Reader(['en'], gpu=False)

def ler_qr_code(img):
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(img)
    return str(data).strip() if data else None

def extrair_valor_hidrometro(img):
    # Processamento focado em dígitos
    resultados = reader.readtext(img)
    for (bbox, text, prob) in resultados:
        # Filtra apenas números com 4 a 6 dígitos (padrão de hidrómetro)
        limpo = re.sub(r'\D', '', text)
        if 4 <= len(limpo) <= 6:
            return limpo
    return None

def processar_leitura_completa(caminho):
    img = cv2.imread(caminho)
    if img is None: return {"status": "Erro"}

    unidade = ler_qr_code(img)
    valor = extrair_valor_hidrometro(img)

    return {
        "unidade": unidade,
        "valor": valor,
        "status": "Sucesso" if unidade and valor else "Parcial"
    }