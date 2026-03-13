import cv2
import pytesseract
import numpy as np
import gc  # Garbage Collector para limpar a RAM
import os
import pytesseract

# Este comando avisa ao Python onde o programa que você acabou de instalar está
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extrair_dados_fluxo(origem):
    """
    MODULARIZADO: Agora aceita tanto um frame (matriz) quanto um caminho de arquivo.
    Explicação: Se 'origem' for um texto (caminho), ele carrega. Se for imagem, processa direto.
    """
    try:
        # Verifica se a origem é um caminho de arquivo (string)
        if isinstance(origem, str):
            if not os.path.exists(origem):
                return None
            frame = cv2.imread(origem)
        else:
            frame = origem

        # 1. Converte para cinza (Reduz 75% do peso da imagem na RAM)
        cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 2. Redimensiona para um tamanho fixo (Leveza para o processador)
        altura, largura = cinza.shape[:2]
        proporcao = 600 / largura
        processavel = cv2.resize(cinza, (600, int(altura * proporcao)))

        # 3. OCR focado apenas em dígitos
        # --psm 7: Trata a imagem como uma única linha de texto
        # whitelist: Ignora letras, foca só em 0-9
        config_ocr = '--psm 7 -c tessedit_char_whitelist=0123456789'
        leitura = pytesseract.image_to_string(processavel, config=config_ocr)

        # Limpeza agressiva da memória RAM
        del cinza
        del processavel
        if isinstance(origem, str):
            del frame
        gc.collect()

        return leitura.strip()
    except Exception as e:
        print(f"Erro no processamento de fluxo: {e}")
        return None
