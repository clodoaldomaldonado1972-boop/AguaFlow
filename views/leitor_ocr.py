import cv2
import pytesseract
import numpy as np
import os

# --- PROTEÇÃO CONTRA ERRO DE DLL (PYZBAR) ---
try:
    from pyzbar import pyzbar
    PYZBAR_AVAILABLE = True
except Exception as e:
    PYZBAR_AVAILABLE = False
    print(f"⚠️ Aviso: Scanner QR desativado (Erro de DLL: {e}).")

# Configuração do Tesseract - Caminho padrão no Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def ler_qr_code(frame):
    """Detecta o QR Code. Se a biblioteca falhar, retorna None para entrada manual."""
    if not PYZBAR_AVAILABLE:
        return None

    try:
        qrcodes = pyzbar.decode(frame)
        for qrcode in qrcodes:
            return qrcode.data.decode('utf-8')
    except:
        return None
    return None


def extrair_dados_fluxo(img):
    """Lógica de OCR com pré-processamento para hidrômetros."""
    try:
        # Converte para escala de cinza
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Aumenta o contraste e limpa ruídos (Thresholding)
        # Isso ajuda o Tesseract a focar apenas nos números pretos
        _, thresh = cv2.threshold(
            gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Configuração: psm 7 (trata a imagem como uma única linha de texto)
        # Whitelist: obriga o Tesseract a procurar apenas números
        config = '--psm 7 -c tessedit_char_whitelist=0123456789'
        texto = pytesseract.image_to_string(thresh, config=config).strip()

        return "Identificado", texto if texto else None
    except Exception as e:
        print(f"❌ Erro no OCR: {e}")
        return "Erro", None


def processar_leitura_completa(caminho_foto):
    """Fluxo principal do Vivere Prudente: QR Code -> OCR -> Flet."""
    try:
        # Carregamento robusto para lidar com acentos em nomes de pastas
        img_array = np.fromfile(caminho_foto, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            return {"unidade": None, "valor": None, "status": "Erro: Falha ao abrir imagem"}

        # 1. Tenta ler o QR Code (Unidade do Apartamento)
        unidade_detectada = ler_qr_code(img)
        _, valor_ocr = extrair_dados_fluxo(img)

        # Lógica de status para a interface Flet
    if unidade_detectada and valor_ocr:
        status = "Sucesso"
    elif unidade_detectada and not valor_ocr:
        status = "Manual"  # QR OK, mas OCR falhou (reflexo no vidro)
    else:
        status = "Falha"

    return {
        "unidade": unidade_detectada,
        "valor": valor_ocr,
        "status": status
    }


if __name__ == "__main__":
    print("--- Testando Fluxo AguaFlow (Modo Simulação) ---")
    # Se não tiver uma imagem real, o sistema apenas retornará o status de erro em vez de fechar
    resultado = processar_leitura_completa("teste_unidade.jpg")
    print(f"Resultado: {resultado}")
