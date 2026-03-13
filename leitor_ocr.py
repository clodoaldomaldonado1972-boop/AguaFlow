import cv2
import pytesseract
import numpy as np
import gc
import os
import re

# Configuração do caminho do executável do Tesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def extrair_dados_fluxo(origem):
    """
    Função Dual: 
    1. Identifica a unidade via QR Code.
    2. Extrai a leitura do visor (6 dígitos) com 2 casas decimais.
    """
    frame_res = None
    binaria = None
    unidade_id = "Não identificado"  # Valor padrão caso não encontre QR Code

    try:
        # --- 1. CARREGAMENTO ROBUSTO ---
        # np.fromfile permite ler arquivos mesmo que a pasta tenha acentos (ex: ÁguaFlow)
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
        # Padronizamos para 1000px de largura para equilibrar precisão do QR Code e velocidade do OCR
        h_orig, w_orig = frame.shape[:2]
        proporcao = 1000 / w_orig
        frame_res = cv2.resize(
            frame, (1000, int(h_orig * proporcao)), interpolation=cv2.INTER_CUBIC)

        # --- 3. DETECÇÃO DO QR CODE (FOTO INTEIRA) ---
        # Convertemos para cinza a imagem completa para o detector de QR Code ter mais contraste
        cinza_total = cv2.cvtColor(frame_res, cv2.COLOR_BGR2GRAY)
        detector = cv2.QRCodeDetector()

        # detectAndDecode tenta localizar e ler o conteúdo do QR Code
        valor_qr, pts, _ = detector.detectAndDecode(cinza_total)

        if valor_qr:
            unidade_id = valor_qr  # Ex: "APTO 102"

        # --- 4. FOCO NO VISOR (ROI - Região de Interesse) ---
        # Cortamos as bordas da imagem para ignorar números de série e códigos de barras externos.
        # Pegamos de 20% a 80% da altura e 10% a 90% da largura.
        h, w = frame_res.shape[:2]
        y1, y2 = int(h * 0.20), int(h * 0.80)
        x1, x2 = int(w * 0.1), int(w * 0.9)
        foco = frame_res[y1:y2, x1:x2]

        # --- 5. PRÉ-PROCESSAMENTO DO VISOR ---
        # Filtro bilateral remove ruído mantendo as bordas dos números nítidas
        cinza_foco = cv2.cvtColor(foco, cv2.COLOR_BGR2GRAY)
        suave = cv2.bilateralFilter(cinza_foco, 9, 75, 75)

        # Binarização de Otsu transforma em Preto e Branco puro
        _, binaria = cv2.threshold(
            suave, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Salva o diagnóstico para conferirmos o que o robô está "vendo"
        cv2.imwrite("visao_do_visor.png", binaria)

        # --- 6. OCR DO CONSUMO ---
        # Whitelist garante que o robô só procure por números, ignorando letras
        config_ocr = '--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789'
        leitura_bruta = pytesseract.image_to_string(binaria, config=config_ocr)

        # REGRAS DE NEGÓCIO:
        # O re.findall busca blocos isolados de 4 a 6 dígitos (ignora séries longas)
        padrao = re.findall(r'\d{4,6}', leitura_bruta)

        if padrao:
            numeros = padrao[0]
            qtd = len(numeros)

            # Formatação: Os últimos 2 dígitos são as casas decimais (roletes vermelhos)
            inteiros = numeros[:-2] if qtd > 2 else "0"
            decimais = numeros[-2:]
            leitura_final = f"{inteiros}.{decimais}"

            return unidade_id, leitura_final

        # Caso encontre o QR mas não os números
        return unidade_id, None

    except Exception as e:
        print(f"Erro técnico no OCR/QR: {e}")
        return None, None
    finally:
        # LIMPEZA DE MEMÓRIA (Essencial para processar 16+ imagens sem travar o PC)
        if frame_res is not None:
            del frame_res
        gc.collect()
