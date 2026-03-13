import cv2
import pytesseract
import numpy as np
import gc
import os

# Configuração do caminho (Verifique se é este mesmo no seu PC)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def extrair_dados_fluxo(origem):
    try:
        # 1. Carrega a imagem
        if isinstance(origem, str):
            if not os.path.exists(origem):
                return None
            frame = cv2.imread(origem)
        else:
            frame = origem

        # 2. Redimensionamento: O Tesseract lê melhor se o número tiver cerca de 30-50px de altura
        altura_original, largura_original = frame.shape[:2]
        proporcao = 800 / largura_original
        frame_res = cv2.resize(
            frame, (800, int(altura_original * proporcao)), interpolation=cv2.INTER_CUBIC)

        # 3. Pré-processamento (Escala de cinza e Nitidez)
        cinza = cv2.cvtColor(frame_res, cv2.COLOR_BGR2GRAY)

        # Filtro para remover ruído mantendo as bordas dos números
        suave = cv2.bilateralFilter(cinza, 9, 75, 75)

        # 4. Binarização (Preto e Branco puro)
        # Usamos o OTSU para decidir o melhor contraste automaticamente
        _, binaria = cv2.threshold(
            suave, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 5. SALVAR DIAGNÓSTICO (Procure este arquivo em C:\ÁguaFlow)
        cv2.imwrite("visao_do_robo.png", binaria)

        # 6. CONFIGURAÇÃO OCR (O segredo do sucesso)
        # --psm 7: Trata a imagem como uma única linha de texto
        # --oem 3: Usa o motor padrão do Tesseract (LTSM)
        config_ocr = '--psm 7 --oem 3 -c tessedit_char_whitelist=0123456789'

        leitura = pytesseract.image_to_string(binaria, config=config_ocr)

        # Limpeza de memória RAM
        del cinza, suave, binaria, frame_res
        gc.collect()

        return leitura.strip()
    except Exception as e:
        print(f"Erro no OCR: {e}")
        return None
