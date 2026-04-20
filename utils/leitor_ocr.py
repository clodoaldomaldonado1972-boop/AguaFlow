import cv2
import easyocr
import re
import numpy as np

# Inicializa o leitor apenas para números (inglês) para economizar memória
# gpu=False é mais seguro para o build inicial do APK
reader = easyocr.Reader(['en'], gpu=False)

def ler_qr_code(img):
    """
    Tenta detectar e decodificar um QR Code na imagem para identificar a unidade.
    """
    detector = cv2.QRCodeDetector()
    data, _, _ = detector.detectAndDecode(img)
    return str(data).strip() if data else None

def extrair_valor_hidrometro(img):
    """
    Processa a imagem para destacar os dígitos e realiza o OCR.
    """
    # 1. PRÉ-PROCESSAMENTO (Melhoria de Contraste)
    # Converte para tons de cinza
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Aplica um filtro para reduzir ruído e destacar os números pretos
    # Isso ajuda muito em hidrômetros com vidro riscado ou sujo
    processed_img = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    # 2. RECONHECIMENTO DE TEXTO
    resultados = reader.readtext(processed_img)
    
    for (bbox, text, prob) in resultados:
        # Filtra apenas o que parece ser um número de leitura
        # Remove caracteres não numéricos (ex: letras ou símbolos lidos por erro)
        limpo = re.sub(r'\D', '', text)
        
        # IHC: Critério de Validação
        # Hidrômetros e medidores de gás geralmente têm entre 4 e 7 dígitos
        if 4 <= len(limpo) <= 7:
            print(f"Número detectado: {limpo} (Confiança: {prob:.2f})")
            return limpo
            
    return None

def processar_leitura_completa(caminho):
    """
    Função principal chamada pelo ScannerAguaFlow.
    Coordena a leitura do QR Code (Unidade) e do Visor (Valor).
    """
    # Carrega a imagem do caminho temporário fornecido pelo FilePicker
    img = cv2.imread(caminho)
    
    if img is None:
        return {"status": "Erro", "mensagem": "Falha ao carregar arquivo de imagem"}

    # Tenta identificar a unidade via QR Code
    unidade = ler_qr_code(img)
    
    # Tenta extrair o valor numérico do visor
    valor = extrair_valor_hidrometro(img)

    # Retorna o dicionário de resultados para a View
    return {
        "unidade": unidade,
        "valor": valor,
        "status": "Sucesso" if unidade and valor else "Parcial"
    }