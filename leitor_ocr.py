import cv2
import pytesseract
import numpy as np
import gc
import os
import re

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def tentar_ocr(imagem, config):
    """Função auxiliar para tentar extrair números de uma imagem tratada"""
    texto = pytesseract.image_to_string(imagem, config=config)
    padrao = re.findall(r'\d{4,6}', texto)
    return padrao[0] if padrao else None


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

        # 2. REDIMENSIONAMENTO (Fixo em 1200px para estabilidade)
        h_orig, w_orig = frame.shape[:2]
        proporcao = 1200 / w_orig
        frame_res = cv2.resize(
            frame, (1200, int(h_orig * proporcao)), interpolation=cv2.INTER_AREA)

        # 3. QR CODE (DUPLA TENTATIVA)
        cinza = cv2.cvtColor(frame_res, cv2.COLOR_BGR2GRAY)
        detector = cv2.QRCodeDetector()
        valor_qr, _, _ = detector.detectAndDecode(cinza)
        if not valor_qr:  # Se falhar, tenta com contraste
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            valor_qr, _, _ = detector.detectAndDecode(clahe.apply(cinza))
        unidade_id = valor_qr if valor_qr else "Não identificado"

        # 4. FOCO NO VISOR
        h, w = frame_res.shape[:2]
        foco = frame_res[int(h*0.25):int(h*0.75), int(w*0.15):int(w*0.85)]
        cinza_foco = cv2.cvtColor(foco, cv2.COLOR_BGR2GRAY)

        # --- 5. O GRANDE TRUQUE: TRIPLA TENTATIVA DE LIMPEZA ---
        config_ocr = '--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789'
        resultado = None

        # TENTATIVA 1: Limpeza suave (Bilateral + Otsu) - Boa para fotos claras
        suave1 = cv2.bilateralFilter(cinza_foco, 9, 75, 75)
        _, bin1 = cv2.threshold(
            suave1, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        resultado = tentar_ocr(bin1, config_ocr)

        # TENTATIVA 2: Se falhou, tenta limpeza pesada (Median Blur) - Boa para sujeira/ruído
        if not resultado:
            suave2 = cv2.medianBlur(cinza_foco, 5)
            _, bin2 = cv2.threshold(
                suave2, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            resultado = tentar_ocr(bin2, config_ocr)
            # Salva a última tentativa para auditoria
            cv2.imwrite("visao_do_visor.png", bin2)
        else:
            cv2.imwrite("visao_do_visor.png", bin1)

        # TENTATIVA 3: Se ainda falhou, tenta Inversão de Cores (Cores negativas) - Boa para reflexos fortes
        if not resultado:
            _, bin3 = cv2.threshold(
                cinza_foco, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            resultado = tentar_ocr(bin3, config_ocr)

        # 6. FORMATAÇÃO FINAL
        if resultado:
            leitura_final = f"{resultado[:-2] if len(resultado) > 2 else '0'}.{resultado[-2:]}"
            return unidade_id, leitura_final

        return unidade_id, None

    except Exception as e:
        print(f"Erro: {e}")
        return None, None
    finally:
        if frame_res is not None:
            del frame_res
        gc.collect()
