import cv2
import pytesseract
import numpy as np
import gc
import os
import re

# Configuração do caminho do motor OCR Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def extrair_dados_fluxo(origem):
    frame_res = None
    unidade_id = "Não identificado"

    try:
        # 1. CARREGAMENTO
        if isinstance(origem, str):
            if not os.path.exists(origem):
                return None, None
            img_array = np.fromfile(origem, np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        else:
            frame = origem

        if frame is None:
            return None, None

        # 2. REDIMENSIONAMENTO
        h_orig, w_orig = frame.shape[:2]
        proporcao = 1200 / w_orig  # Aumentei um pouco para ajudar o QR Code
        frame_res = cv2.resize(
            frame, (1200, int(h_orig * proporcao)), interpolation=cv2.INTER_CUBIC)

        # 3. DETECÇÃO DO QR CODE (OpenCV com pré-tratamento)
        cinza = cv2.cvtColor(frame_res, cv2.COLOR_BGR2GRAY)
        # Aplicamos um leve brilho para compensar sombras nas fotos reais
        cinza_claro = cv2.convertScaleAbs(cinza, alpha=1.2, beta=30)

        detector = cv2.QRCodeDetector()
        valor_qr, pts, _ = detector.detectAndDecode(cinza_claro)

        if valor_qr:
            unidade_id = valor_qr

        # 4. FOCO NO VISOR
        h, w = frame_res.shape[:2]
        foco = frame_res[int(h*0.25):int(h*0.75), int(w*0.15):int(w*0.85)]

        # 5. PRÉ-PROCESSAMENTO OCR
        cinza_foco = cv2.cvtColor(foco, cv2.COLOR_BGR2GRAY)
        suave = cv2.bilateralFilter(cinza_foco, 9, 75, 75)
        _, binaria = cv2.threshold(
            suave, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        cv2.imwrite("visao_do_visor.png", binaria)

        # 6. OCR DO CONSUMO
        config_ocr = '--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789'
        leitura_bruta = pytesseract.image_to_string(binaria, config=config_ocr)
        padrao = re.findall(r'\d{4,6}', leitura_bruta)

        if padrao:
            numeros = padrao[0]
            leitura_final = f"{numeros[:-2] if len(numeros) > 2 else '0'}.{numeros[-2:]}"
            return unidade_id, leitura_final

        return unidade_id, None

    except Exception as e:
        print(f"Erro: {e}")
        return None, None
    finally:
        if frame_res is not None:
            del frame_res
        gc.collect()
