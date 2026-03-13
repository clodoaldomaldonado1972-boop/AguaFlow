import cv2
import os


def processar_leitura_imagem(caminho_imagem):
    try:
        # Carrega a imagem do hidrômetro
        img = cv2.imread(caminho_imagem)

        # Reduz a imagem para 800px de largura (isso mata o erro de memória)
        altura, largura = img.shape[:2]
        proporcao = 800 / largura
        img_leve = cv2.resize(img, (800, int(altura * proporcao)))

        # Salva a imagem leve por cima da pesada antes de ler
        cv2.imwrite(caminho_imagem, img_leve)

        print("✅ Imagem otimizada para economia de memória.")

        # Aqui continuaria o seu código de leitura (pytesseract ou easyocr)
        # ...
        return "00000"  # Exemplo de retorno
    except Exception as e:
        print(f"Erro: {e}")
        return None
