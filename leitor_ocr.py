import cv2
import pytesseract
import numpy as np
import gc
import os

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def extrair_dados_fluxo(origem):
    try:
        if isinstance(origem, str):
            if not os.path.exists(origem):
                return None
            frame = cv2.imread(origem)
        else:
            frame = origem

        # 1. Converte para escala de cinza
        cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 2. Aumenta o contraste e remove ruído (Filtro Bilateral)
        # Isso mantém as bordas dos números nítidas
        suave = cv2.bilateralFilter(cinza, 9, 75, 75)

        # 3. Transforma em Preto e Branco puro (Threshold)
        _, binaria = cv2.threshold(
            suave, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 4. SALVAR TESTE: Cria um arquivo para você ver o que o Python está lendo
        cv2.imwrite("visao_do_robo.png", binaria)

        # 5. OCR com configuração de "Dígitos Apenas"
        config_ocr = '--psm 7 -c tessedit_char_whitelist=0123456789'
        leitura = pytesseract.image_to_string(binaria, config=config_ocr)

        # Limpeza de memória
        del cinza, suave, binaria
        gc.collect()

        return leitura.strip()
    except Exception as e:
        print(f"Erro no OCR: {e}")
        return None
