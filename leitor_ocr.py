import cv2
import pytesseract
import numpy as np
import gc
import os
import re

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def extrair_dados_fluxo(origem):
    frame_res = None
    binaria = None
    unidade_id = "Não identificado"

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

        # 2. REDIMENSIONAMENTO
        h_orig, w_orig = frame.shape[:2]
        proporcao = 1000 / w_orig  # Aumentamos um pouco para ajudar no QR Code
        frame_res = cv2.resize(
            frame, (1000, int(h_orig * proporcao)), interpolation=cv2.INTER_CUBIC)

        # 3. DETECÇÃO DO QR CODE (Identificação do Apto)
        # Tentamos ler em tons de cinza para aumentar a precisão
        cinza_total = cv2.cvtColor(frame_res, cv2.COLOR_BGR2GRAY)
        detector = cv2.QRCodeDetector()
        valor_qr, pts, _ = detector.detectAndDecode(cinza_total)

        if valor_qr:
            unidade_id = valor_qr
            # print(f"📍 Unidade Identificada: {unidade_id}") # Removido para limpar a tela

        # 4. FOCO NO VISOR (ROI MAIS AMPLO)
        # Aumentamos a área de busca para 20% até 80% da altura
        h, w = frame_res.shape[:2]
        y1, y2 = int(h * 0.20), int(h * 0.80)
        x1, x2 = int(w * 0.1), int(w * 0.9)
        foco = frame_res[y1:y2, x1:x2]

        # 5. PRÉ-PROCESSAMENTO DO VISOR
        cinza = cv2.cvtColor(foco, cv2.COLOR_BGR2GRAY)
        suave = cv2.bilateralFilter(cinza, 9, 75, 75)
        _, binaria = cv2.threshold(
            suave, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Salva o que o robô está focando para você conferir
        cv2.imwrite("visao_do_visor.png", binaria)

        # 6. OCR DO CONSUMO
        config_ocr = '--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789'
        leitura_bruta = pytesseract.image_to_string(binaria, config=config_ocr)

        # Busca bloco de 4 a 6 dígitos
        padrao = re.findall(r'\d{4,6}', leitura_bruta)

        if padrao:
            numeros = padrao[0]
            qtd = len(numeros)
            inteiros = numeros[:-2] if qtd > 2 else "0"
            decimais = numeros[-2:]
            leitura_final = f"{inteiros}.{decimais}"

            # Retorna uma tupla com (ID do Apto, Valor da Leitura)
            return unidade_id, leitura_final

        return unidade_id, None

    except Exception as e:
        print(f"Erro no OCR/QR: {e}")
        return None, None
    finally:
        if frame_res is not None:
            del frame_res
        gc.collect()
