import cv2
import pytesseract
import numpy as np
import gc
import os

# Configuração do caminho do executável do Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def extrair_dados_fluxo(origem):
    """
    Processa a imagem e retorna o valor formatado com 2 casas decimais (max 6 dígitos).
    """
    frame_res = None
    binaria = None

    try:
        # 1. CARREGAMENTO
        if isinstance(origem, str):
            if not os.path.exists(origem):
                return None
            img_array = np.fromfile(origem, np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        else:
            frame = origem

        if frame is None:
            return None

        # 2. REDIMENSIONAMENTO E CINZA
        h_orig, w_orig = frame.shape[:2]
        proporcao = 800 / w_orig
        frame_res = cv2.resize(
            frame, (800, int(h_orig * proporcao)), interpolation=cv2.INTER_CUBIC)
        cinza = cv2.cvtColor(frame_res, cv2.COLOR_BGR2GRAY)
        suave = cv2.bilateralFilter(cinza, 9, 75, 75)

        # 3. BINARIZAÇÃO
        _, binaria = cv2.threshold(
            suave, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        cv2.imwrite("visao_do_robo.png", binaria)

        # 4. OCR
        config_ocr = '--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789'
        leitura_bruta = pytesseract.image_to_string(binaria, config=config_ocr)

        # 5. FILTRAGEM E REGRA DE NEGÓCIO (6 DÍGITOS + 2 DECIMAIS)
        numeros = "".join(filter(str.isdigit, leitura_bruta))
        qtd = len(numeros)

        if 3 <= qtd <= 6:
            inteiros = numeros[:-2]
            decimais = numeros[-2:]

            if not inteiros:
                inteiros = "0"

            return f"{inteiros}.{decimais}"

        elif qtd > 6:
            print(f"⚠️ Ignorado: {qtd} dígitos (Provável nº série).")
            return None

        return None

    except Exception as e:
        print(f"Erro técnico no OCR: {e}")
        return None

    finally:
        # LIMPEZA DE MEMÓRIA
        if frame_res is not None:
            del frame_res
        if binaria is not None:
            del binaria
        gc.collect()
