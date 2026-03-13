import cv2
import pytesseract
import numpy as np
import gc
import os

# Configuração do caminho do Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def extrair_dados_fluxo(origem):
    # Inicializamos as variáveis como None para evitar o erro de "local variable"
    frame_res = None
    cinza = None
    suave = None
    binaria = None

    try:
        # 1. Carrega a imagem
        if isinstance(origem, str):
            if not os.path.exists(origem):
                return None
            frame = cv2.imread(origem)
        else:
            frame = origem

        if frame is None:
            return None

        # 2. Redimensionamento inteligente
        altura_original, largura_original = frame.shape[:2]
        proporcao = 800 / largura_original
        frame_res = cv2.resize(
            frame, (800, int(altura_original * proporcao)), interpolation=cv2.INTER_CUBIC)

        # 3. Pré-processamento
        cinza = cv2.cvtColor(frame_res, cv2.COLOR_BGR2GRAY)
        suave = cv2.bilateralFilter(cinza, 9, 75, 75)

        # 4. Binarização (Threshold)
        _, binaria = cv2.threshold(
            suave, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Engrossar um pouco os números para o Tesseract ler melhor
        kernel = np.ones((2, 2), np.uint8)
        binaria = cv2.erode(binaria, kernel, iterations=1)

        # 5. Salva diagnóstico (Sempre gera para podermos ver o erro)
        cv2.imwrite("visao_do_robo.png", binaria)

        # 6. CONFIGURAÇÃO OCR (Calibrada para maior sensibilidade)
        # Trocamos --psm 7 (linha única) por --psm 6 (bloco de texto)
        # Isso ajuda se a foto não estiver perfeitamente reta.
        config_ocr = '--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789'

        leitura = pytesseract.image_to_string(binaria, config=config_ocr)

        return leitura.strip()

    except Exception as e:
        print(f"Erro no OCR: {e}")
        return None
    finally:
        # Limpeza segura: Só deleta se a variável realmente existir
        for var in [frame_res, cinza, suave, binaria]:
            if var is not None:
                del var
        gc.collect()
