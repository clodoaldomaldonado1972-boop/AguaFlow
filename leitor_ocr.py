import cv2
import pytesseract
import numpy as np
import gc  # Garbage Collector para limpar a RAM


def extrair_dados_fluxo(frame_camera):
    """
    Recebe um frame direto da câmera, processa e extrai números.
    Não salva arquivo no HD, economizando memória e evitando o MemoryError.
    """
    try:
        # 1. Converte para cinza (Reduz 75% do peso da imagem na RAM)
        cinza = cv2.cvtColor(frame_camera, cv2.COLOR_BGR2GRAY)

        # 2. Redimensiona para um tamanho fixo de processamento leve
        altura, largura = cinza.shape[:2]
        proporcao = 600 / largura
        processavel = cv2.resize(cinza, (600, int(altura * proporcao)))

        # 3. OCR focado apenas em dígitos (Aumenta velocidade e precisão)
        config_ocr = '--psm 7 -c tessedit_char_whitelist=0123456789'
        leitura = pytesseract.image_to_string(processavel, config=config_ocr)

        # Limpeza agressiva: remove objetos pesados da memória
        del cinza
        del processavel
        gc.collect()

        return leitura.strip()
    except Exception as e:
        print(f"Erro no processamento de fluxo: {e}")
        return None
