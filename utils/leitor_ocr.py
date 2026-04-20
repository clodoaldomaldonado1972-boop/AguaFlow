import cv2
import easyocr
import re
import numpy as np

# Inicializa o leitor globalmente para evitar recarregar o modelo em cada foto
# gpu=False garante compatibilidade em PCs sem placa de vídeo dedicada
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
    # 1. PRÉ-PROCESSAMENTO (Melhoria de Contraste para hidrômetros)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Redução de ruído (Bilateral Filter mantém as bordas dos números nítidas)
    denoised = cv2.bilateralFilter(gray, 9, 75, 75)
    
    # Limiarização adaptativa para lidar com sombras no vidro do medidor
    processed_img = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    # 2. RECONHECIMENTO DE TEXTO
    resultados = reader.readtext(processed_img)
    
    for (bbox, text, prob) in resultados:
        # Remove qualquer caractere que não seja número ou ponto/vírgula
        limpo = re.sub(r'[^\d.,]', '', text)
        
        # IHC: Critério de Validação para medidores reais
        # Geralmente entre 4 e 8 caracteres numéricos
        if 4 <= len(re.sub(r'\D', '', limpo)) <= 8:
            print(f"[OCR] Sucesso: {limpo} (Confiança: {prob:.2f})")
            return limpo.replace(',', '.') # Padroniza para formato float
            
    return None

def processar_leitura_completa(caminho):
    """
    Função principal chamada pelo ScannerAguaFlow no views/medicao.py.
    """
    img = cv2.imread(caminho)
    
    if img is None:
        return {"status": "Erro", "mensagem": "Falha ao carregar arquivo de imagem"}

    # Tentativa 1: Identificar unidade via QR Code (Se colado no hidrômetro)
    unidade_detectada = ler_qr_code(img)
    
    # Tentativa 2: Extrair valor numérico do visor
    valor_detectado = extrair_valor_hidrometro(img)

    if valor_detectado:
        return {
            "status": "Sucesso",
            "unidade": unidade_detectada, # Pode ser None se não houver QR Code
            "leitura": valor_detectado,
            "mensagem": "Leitura processada com sucesso!"
        }
    else:
        return {
            "status": "Aviso",
            "mensagem": "Não foi possível extrair um valor confiável. Tente focar mais no visor."
        }