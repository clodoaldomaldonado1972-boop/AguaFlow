import cv2
import numpy as np
import gc  # Coletor de lixo para limpar a memória RAM


def ler_hidrometro_fluxo(frame_da_camera):
    try:
        # 1. Converte o frame para escala de cinza (ocupa 3x menos memória)
        gray = cv2.cvtColor(frame_da_camera, cv2.COLOR_BGR2GRAY)

        # 2. Localiza onde estão os números (Processamento leve)
        # Aqui entra a sua lógica de OCR (Tesseract ou EasyOCR)
        valor_detectado = seu_motor_ocr.read(gray)

        # 3. LIMPEZA AGRESSIVA DE MEMÓRIA
        del gray
        gc.collect()  # Força o Python a liberar a RAM na hora

        return valor_detectado
    except Exception as e:
        print(f"Erro no fluxo: {e}")
        return None
