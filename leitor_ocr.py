import cv2
import pytesseract  # Ou a biblioteca que você estiver usando
import numpy as np
import os


def processar_leitura_imagem(caminho_imagem):
    try:
        # 1. Verifica se o arquivo existe para não travar
        if not os.path.exists(caminho_imagem):
            print("❌ Erro: Arquivo de imagem não encontrado.")
            return None

        # 2. Carrega a imagem
        img = cv2.imread(caminho_imagem)
        if img is None:
            print("❌ Erro ao carregar a imagem (formato inválido).")
            return None

        # 3. REDIMENSIONAMENTO (O remédio para a falta de memória)
        # Se a imagem for maior que 1000 pixels, reduzimos para 1000px mantendo a proporção
        altura, largura = img.shape[:2]
        if largura > 1000:
            proporcao = 1000 / largura
            novo_tamanho = (1000, int(altura * proporcao))
            img = cv2.resize(img, novo_tamanho, interpolation=cv2.INTER_AREA)
            print(
                f"✅ Imagem redimensionada para {novo_tamanho[0]}x{novo_tamanho[1]}")

        # 4. PRÉ-PROCESSAMENTO (Para ajudar o OCR a ler melhor)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # Converte para cinza
        # Aplica um filtro para aumentar o contraste (ajuda em hidrômetros sujos)
        _, threshold = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 5. EXECUÇÃO DO OCR (A leitura propriamente dita)
        # Ajuste o comando abaixo de acordo com sua biblioteca (Tesseract/EasyOCR)
        # Exemplo com Tesseract:
        resultado = pytesseract.image_to_string(
            threshold, config='--psm 7 digits')

        # Limpa o resultado para pegar apenas números
        valor_limpo = "".join(filter(str.isdigit, resultado))

        print(f"🔍 Valor detectado pelo OCR: {valor_limpo}")
        return valor_limpo if valor_limpo else None

    except Exception as e:
        print(f"❌ Erro crítico no OCR: {e}")
        return None
