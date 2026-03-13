import cv2
import pytesseract
import numpy as np
import gc
import os
import re

# Configuração do caminho do motor OCR Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def extrair_dados_fluxo(origem):
    """
    Motor Dual do Água Flow:
    1. Escaneia a imagem inteira em busca de QR Code (Identificação).
    2. Recorta o centro da imagem para focar no visor (Consumo).
    3. Formata o consumo com 2 casas decimais seguindo o padrão de 6 campos.
    """
    frame_res = None
    binaria = None
    unidade_id = "Não identificado"

    try:
        # --- 1. CARREGAMENTO ROBUSTO ---
        # np.fromfile é usado para evitar erros com acentos no caminho das pastas
        if isinstance(origem, str):
            if not os.path.exists(origem):
                return None, None
            img_array = np.fromfile(origem, np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        else:
            frame = origem

        if frame is None:
            return None, None

        # --- 2. REDIMENSIONAMENTO ---
        # Usamos 1000px de largura para dar mais clareza ao QR Code sem pesar a memória
        h_orig, w_orig = frame.shape[:2]
        proporcao = 1000 / w_orig
        frame_res = cv2.resize(
            frame, (1000, int(h_orig * proporcao)), interpolation=cv2.INTER_CUBIC)

        # --- 3. DETECÇÃO DO QR CODE (VISÃO TOTAL) ---
        # Primeiro tentamos ler o QR Code na imagem inteira antes de qualquer corte
        cinza_total = cv2.cvtColor(frame_res, cv2.COLOR_BGR2GRAY)
        detector = cv2.QRCodeDetector()
        valor_qr, pts, _ = detector.detectAndDecode(cinza_total)

        if valor_qr:
            unidade_id = valor_qr

        # --- 4. FOCO NO VISOR (ROI - REGION OF INTEREST) ---
        # Criamos uma "janela" de foco para ignorar números de série e códigos de barras
        # Focamos entre 20% e 80% da altura para garantir que o visor seja capturado
        h, w = frame_res.shape[:2]
        y1, y2 = int(h * 0.20), int(h * 0.80)
        x1, x2 = int(w * 0.1), int(w * 0.9)
        foco = frame_res[y1:y2, x1:x2]

        # --- 5. PRÉ-PROCESSAMENTO PARA OCR ---
        # Filtro Bilateral: limpa o ruído da foto mas mantém as bordas dos números nítidas
        cinza_foco = cv2.cvtColor(foco, cv2.COLOR_BGR2GRAY)
        suave = cv2.bilateralFilter(cinza_foco, 9, 75, 75)

        # Binarização de Otsu: transforma a imagem em P&B puro (números pretos, fundo branco)
        _, binaria = cv2.threshold(
            suave, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Salva o diagnóstico visual (importante para conferir o que o robô está lendo)
        cv2.imwrite("visao_do_visor.png", binaria)

        # --- 6. OCR E REGRAS DE NEGÓCIO ---
        # PSM 6: Trata o visor como um bloco de texto uniforme
        config_ocr = '--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789'
        leitura_bruta = pytesseract.image_to_string(binaria, config=config_ocr)

        # Regex: Busca apenas sequências entre 4 e 6 dígitos (ignora o número de série longo)
        padrao = re.findall(r'\d{4,6}', leitura_bruta)

        if padrao:
            numeros = padrao[0]
            qtd = len(numeros)

            # Formatação Decimal: Separa os últimos 2 dígitos como decimais
            inteiros = numeros[:-2] if qtd > 2 else "0"
            decimais = numeros[-2:]
            leitura_final = f"{inteiros}.{decimais}"

            return unidade_id, leitura_final

        return unidade_id, None

    except Exception as e:
        print(f"Erro no OCR/QR: {e}")
        return None, None
    finally:
        # Coleta de lixo para manter o sistema leve
        if frame_res is not None:
            del frame_res
        gc.collect()
