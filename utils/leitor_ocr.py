import cv2
import pytesseract
import numpy as np
import os
import easyocr
import re

# --- CONFIGURAÇÃO DO AMBIENTE ---
tesseract_path = os.getenv("TESSERACT_PATH", r'C:\Program Files\Tesseract-OCR\tesseract.exe')
pytesseract.pytesseract.tesseract_cmd = tesseract_path

# Inicializar EasyOCR (English para números)
reader = easyocr.Reader(['en'], gpu=False)

def carregar_imagem(caminho_ou_img):
    """Garante que a entrada seja um numpy array válido para o OpenCV."""
    if isinstance(caminho_ou_img, str):
        img = cv2.imread(caminho_ou_img)
        if img is None:
            print(f"Erro: Não foi possível carregar a imagem em {caminho_ou_img}")
        return img
    return caminho_ou_img

def ler_qr_code(img):
    """Lê o QR Code para identificar a unidade (Apto)."""
    try:
        img = carregar_imagem(img)
        detector = cv2.QRCodeDetector()
        # detectAndDecode agora recebe o numpy array corretamente
        data, bbox, straight_qrcode = detector.detectAndDecode(img)
        if data:
            return str(data).strip()
    except Exception as e:
        print(f"Erro ao ler QR code: {e}")
    return None

def extrair_dados_fluxo(img, unidade_qr=None):
    try:
        img = carregar_imagem(img)
        # 1. Converter para tons de cinza
        # No leitor_ocr.py, dentro de extrair_dados_fluxo:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Filtro para destacar números pretos e ignorar reflexos no vidro
        processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

        results = reader.readtext(processed)
        
        for res in results:
            texto = res[1]
            numeros = re.sub(r'[^0-9]', '', texto)
            
            # Ignora se for o número da unidade (adesivo do QR)
            if unidade_qr and numeros == str(unidade_qr):
                continue
            
            # Hidrómetros costumam ter entre 4 a 6 dígitos pretos
            if 4 <= len(numeros) <= 6:
                return numeros
        return None
    
    except Exception as e:
        print(f"Erro no processamento OCR: {e}")
        return None

def processar_leitura_completa(caminho_arquivo):
    """
    Função principal chamada pelo scanner.py.
    Recebe o caminho do arquivo e retorna o dicionário de status.
    """
    try:
        img = carregar_imagem(caminho_arquivo)
        if img is None:
            return {"unidade": None, "valor": None, "status": "Erro", "pode_inserir_manual": True}

        # 1. Identificar Unidade via QR Code
        unidade = ler_qr_code(img)

        # 2. Extrair Valor do Hidrômetro (passando a unidade para evitar duplicidade)
        valor_ocr = extrair_dados_fluxo(img, unidade_qr=unidade)

        # 3. Definir Status do Processamento
        if unidade and valor_ocr:
            status = "Sucesso"
            manual = False
        elif unidade:
            status = "OCR_Falhou" # Leu o QR mas não o número
            manual = True
        else:
            status = "Manual" # Não leu nada
            manual = True

        return {
            "unidade": unidade,
            "valor": valor_ocr,
            "status": status,
            "pode_inserir_manual": manual
        }

    except Exception as e:
        print(f"Falha crítica no processamento: {e}")
        return {"unidade": None, "valor": None, "status": "Erro", "pode_inserir_manual": True}