import cv2
import pytesseract
import numpy as np
import os
import easyocr
import re

# Configuração do Tesseract
tesseract_path = os.getenv(
    "TESSERACT_PATH", r'C:\Program Files\Tesseract-OCR\tesseract.exe')
pytesseract.pytesseract.tesseract_cmd = tesseract_path

# Inicializar EasyOCR
# Use GPU if available, but False for CPU
reader = easyocr.Reader(['en'], gpu=False)


def ler_qr_code(img):
    """Implementar leitura de QR code usando OpenCV."""
    try:
        detector = cv2.QRCodeDetector()
        data, bbox, straight_qrcode = detector.detectAndDecode(img)
        if data:
            return data
    except Exception as e:
        print(f"Erro ao ler QR code: {e}")
    return None


def extrair_dados_fluxo(img):
    """Implementar extração de dados do medidor usando EasyOCR."""
    try:
        # Usar EasyOCR para detectar texto
        results = reader.readtext(img)

        # Extrair todos os textos detectados
        textos = [result[1] for result in results]

        # Procurar por valores numéricos (leitura do medidor)
        valor = None
        for texto in textos:
            # Procurar por números com ponto decimal (ex: 123.45)
            matches = re.findall(r'\d+\.\d+', texto)
            if matches:
                valor = matches[0]  # Pegar o primeiro encontrado
                break
            # Se não encontrar decimal, procurar por números inteiros
            matches = re.findall(r'\d+', texto)
            if matches:
                valor = matches[0]
                break

        # Para unidade, talvez procurar por "Apto" ou similar, mas por enquanto None
        unidade = None
        for texto in textos:
            if "Apto" in texto:
                unidade = texto
                break

        return unidade, valor
    except Exception as e:
        print(f"Erro ao extrair dados: {e}")
        return None, None


def processar_leitura_completa(img):
    """
    Processa a imagem completa: lê QR code e depois extrai valor do medidor.
    Retorna dict com status detalhado para o fluxo de confirmação.
    """
    try:
        if img is None:
            return {"unidade": None, "valor": None, "status": "Erro", "pode_inserir_manual": False}

        # Etapa 1: Tentar ler QR code
        unidade_detectada = ler_qr_code(img)

        # Etapa 2: Extrair valor do medidor
        _, valor_ocr = extrair_dados_fluxo(img)

        # Determinar status e se permite entrada manual
        if valor_ocr:
            status = "Sucesso"
            pode_inserir_manual = False
        else:
            # OCR falhou, mas permite entrada manual
            status = "OCR_Falhou"
            pode_inserir_manual = True

        return {
            "unidade": unidade_detectada,
            "valor": valor_ocr,
            "status": status,
            "pode_inserir_manual": pode_inserir_manual
        }
    except Exception as e:
        print(f"Erro ao processar leitura: {e}")
        return {"unidade": None, "valor": None, "status": f"Erro: {e}", "pode_inserir_manual": True}
