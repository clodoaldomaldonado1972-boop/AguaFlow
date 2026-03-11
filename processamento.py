import cv2
import pytesseract
import numpy as np
from pyzbar.pyzbar import decode

# Substitua o detector do OpenCV por isso:
resultado_qr = decode(img)
if resultado_qr:
    dados_qr = resultado_qr[0].data.decode('utf-8')

# Aponte o caminho se o Tesseract não estiver no PATH do Windows
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def processar_foto_hidrometro(caminho_foto):
    # 1. Carrega a imagem
    img = cv2.imread(caminho_foto)
    if img is None:
        return None, None

    # --- OTIMIZAÇÃO PARA MOBILE (Redimensionamento) ---
    # Fotos de 50MP travam o OCR. Redimensionamos para uma largura padrão de 1280px.
    altura, largura = img.shape[:2]
    proporcao = 1280 / largura
    img = cv2.resize(img, (1280, int(altura * proporcao)))

    # Aumenta o contraste para o QR Code (ajuda se o código estiver desbotado)
    img_qr = cv2.convertScaleAbs(img, alpha=1.5, beta=0)
    dados_qr, _, _ = detector.detectAndDecode(img_qr)

    # --- ETAPA A: QR CODE (Tentar no original e no cinza) ---
    detector = cv2.QRCodeDetector()
    dados_qr, _, _ = detector.detectAndDecode(img)

    # --- ETAPA B: OCR (Melhoria de Contraste para Subsolo) ---
    cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Suaviza o ruído antes de binarizar (essencial para fotos de celular)
    suave = cv2.GaussianBlur(cinza, (5, 5), 0)

    # Threshold Adaptativo (Melhor que o Otsu para luz irregular)
    binaria = cv2.adaptiveThreshold(
        suave, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 11, 2
    )

    # Dilatação: Engrossa os números para o Tesseract ler melhor
    kernel = np.ones((2, 2), np.uint8)
    binaria = cv2.dilate(binaria, kernel, iterations=1)

    # Configuração do Tesseract
    # --psm 7: Trata a imagem como uma única linha de texto
    # --oem 3: Usa o motor padrão (LSTM)
    config_ocr = '--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789'

    try:
        leitura_texto = pytesseract.image_to_string(binaria, config=config_ocr)
    except Exception as e:
        print(f"Erro no Tesseract: {e}")
        leitura_texto = ""

    # Limpeza final: remove espaços e caracteres estranhos
    valor_final = "".join(filter(str.isdigit, leitura_texto))

    print(f"🔍 Debug AguaFlow - QR: {dados_qr} | Valor: {valor_final}")

    return dados_qr if dados_qr else None, valor_final if valor_final else None
