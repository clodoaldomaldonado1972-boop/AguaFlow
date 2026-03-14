import cv2
import pytesseract
import numpy as np
import os
import re

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def processar_e_ler(imagem):
    """Configuração otimizada para leitura de dígitos em hidrômetros"""
    config = '--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789'
    texto = pytesseract.image_to_string(imagem, config=config)
    # Filtra sequências de 4 a 7 dígitos
    busca = re.findall(r'\d{4,7}', texto)
    return busca[0] if busca else None


def extrair_dados_fluxo(origem):
    try:
        if isinstance(origem, str):
            img_array = np.fromfile(origem, np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        else:
            frame = origem
        if frame is None:
            return None, None

        h_f, w_f = frame.shape[:2]

        # --- ESTRATÉGIA EM CASCATA ---
        # 1. Tentativa com FOCO CENTRAL (Evita seriais e marcas)
        corte_focado = frame[int(h_f*0.35):int(h_f*0.75),
                             int(w_f*0.10):int(w_f*0.90)]

        # 2. Tentativa com FOTO INTEIRA (Caso o visor esteja fora do centro)
        tentativas = [corte_focado, frame]

        for img_alvo in tentativas:
            cinza = cv2.cvtColor(img_alvo, cv2.COLOR_BGR2GRAY)
            cinza = cv2.resize(cinza, None, fx=2, fy=2,
                               interpolation=cv2.INTER_CUBIC)

            # Teste A: Otsu Normal
            _, t1 = cv2.threshold(
                cinza, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            res = processar_e_ler(t1)
            if res:
                cv2.imwrite("visao_do_visor.png", t1)
                return "Identificado", res

            # Teste B: Adaptativo Invertido
            t2 = cv2.adaptiveThreshold(cinza, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, 25, 11)
            res = processar_e_ler(t2)
            if res:
                cv2.imwrite("visao_do_visor.png", t2)
                return "Identificado", res

        return "Não identificado", None

    except Exception as e:
        print(f"Erro: {e}")
        return None, None
