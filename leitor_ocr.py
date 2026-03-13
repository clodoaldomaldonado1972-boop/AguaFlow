import cv2
import pytesseract
import re
import numpy as np

# Se o Tesseract não estiver no PATH, descomente e ajuste:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def processar_leitura_imagem(caminho_arquivo):
    """Recebe o caminho de uma foto e extrai os números."""
    try:
        # 1. Carrega a imagem que o usuário acabou de tirar no celular
        img = cv2.imread(caminho_arquivo)
        if img is None:
            return ""

        # 2. Processamento (Cinza e Contraste) - Mantendo sua lógica excelente
        cinza = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Otimização: Aumentar um pouco a imagem ajuda o Tesseract a ler melhor
        cinza = cv2.resize(cinza, None, fx=2, fy=2,
                           interpolation=cv2.INTER_CUBIC)

        # Aplicando threshold (ajuste o 150 se a foto sair muito clara/escura)
        _, threshold = cv2.threshold(cinza, 150, 255, cv2.THRESH_BINARY)

        # 3. OCR (Configurado para dígitos)
        # Usamos psm 6 ou 7 conforme seus testes
        texto = pytesseract.image_to_string(threshold, config='--psm 7 digits')

        # 4. Limpeza (pega apenas números)
        leitura_final = "".join(re.findall(r'\d+', texto))

        print(f"🔍 OCR Detectou: {leitura_final}")
        return leitura_final

    except Exception as e:
        print(f"❌ Erro no processamento OCR: {e}")
        return ""
