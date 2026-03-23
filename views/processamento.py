import cv2
import pytesseract
import numpy as np

# Se necessário no Windows, descomente e aponte o caminho do executável:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def processar_foto_hidrometro(caminho_foto):
    # 1. Carregar a imagem
    img = cv2.imread(caminho_foto)
    if img is None:
        return None, None

    # Redimensionar para facilitar o processamento (Padrão HD)
    largura_alvo = 1280
    fator = largura_alvo / img.shape[1]
    img = cv2.resize(img, (largura_alvo, int(img.shape[0] * fator)))

    # --- ETAPA A: QR CODE (Multicamadas) ---
    detector = cv2.QRCodeDetector()
    dados_qr, _, _ = detector.detectAndDecode(img)

    if not dados_qr:
        # Aumenta contraste e converte para cinza para tentar o QR novamente
        img_contraste = cv2.convertScaleAbs(img, alpha=1.5, beta=10)
        dados_qr, _, _ = detector.detectAndDecode(img_contraste)

    # --- ETAPA B: OCR (Pré-processamento Avançado) ---
    cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Blur para reduzir ruído digital (ISO alto do celular no escuro)
    blur = cv2.medianBlur(cinza, 3)

    # Threshold Adaptativo: Crucial para lidar com a lanterna do celular refletindo no vidro
    binaria = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 11, 2
    )

    # Operação Morfológica (Dilação): Conecta partes separadas dos números
    kernel = np.ones((2, 2), np.uint8)
    binaria = cv2.dilate(binaria, kernel, iterations=1)

    # Configuração Tesseract:
    # PSM 7: Trata a imagem como uma única linha de texto.
    # OEM 3: Modo de motor padrão (LSTM).
    config_ocr = '--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789'

    try:
        leitura_texto = pytesseract.image_to_string(binaria, config=config_ocr)
        # Filtra apenas dígitos para evitar sujeira de caracteres especiais
        valor_final = "".join(filter(str.isdigit, leitura_texto))
    except Exception as e:
        print(f"❌ Erro OCR: {e}")
        valor_final = ""

    print(f"🔍 DEBUG AGUA FLOW - QR: {dados_qr} | Valor: {valor_final}")

    return dados_qr if dados_qr else None, valor_final if valor_final else None
