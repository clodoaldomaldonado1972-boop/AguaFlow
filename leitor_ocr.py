import cv2
import pytesseract
import numpy as np
import os


def processar_leitura_imagem(caminho_imagem):
    try:
        if not os.path.exists(caminho_imagem):
            return None

        # 1. Carrega a imagem (Aqui é onde o erro de memória costuma dar)
        img = cv2.imread(caminho_imagem)
        if img is None:
            return None

        # 2. REDIMENSIONAR (Crucial para evitar falta de memória)
        # Se a largura for maior que 1000px, reduzimos para 1000px mantendo a proporção
        altura, largura = img.shape[:2]
        if largura > 1000:
            proporcao = 1000 / largura
            novo_tamanho = (1000, int(altura * proporcao))
            # O interpolation=cv2.INTER_AREA é o melhor para diminuir fotos
            img = cv2.resize(img, novo_tamanho, interpolation=cv2.INTER_AREA)
            print(
                f"✅ Foto redimensionada para {novo_tamanho[0]}x{novo_tamanho[1]} (Economia de RAM)")

        # 3. PRÉ-PROCESSAMENTO (Fica mais rápido com a imagem menor)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Filtro para destacar os números pretos no hidrômetro
        _, threshold = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 4. OCR (Leitura dos números)
        resultado = pytesseract.image_to_string(
            threshold, config='--psm 7 digits')

        # Limpa para deixar só números
        valor_limpo = "".join(filter(str.isdigit, resultado))

        print(f"🔍 Valor detectado: {valor_limpo}")
        return valor_limpo if valor_limpo else None

    except Exception as e:
        print(f"❌ Erro no OCR: {e}")
        return None
