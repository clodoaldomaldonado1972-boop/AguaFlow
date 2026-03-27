import cv2
import pytesseract
import numpy as np
import os
import re

# 1. Configuração do Caminho do Tesseract (Ajuste se o seu Windows for diferente)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def processar_e_ler(imagem):
    """
    Recebe uma imagem binarizada e tenta extrair apenas os números.
    --psm 6: Assume que a imagem é um bloco de texto único e uniforme (ideal para visores).
    """
    config = '--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789'
    
    # Executa o OCR
    texto = pytesseract.image_to_string(imagem, config=config)
    
    # Filtra apenas sequências de 4 a 7 dígitos (padrão de hidrômetros)
    # Isso ignora sujeiras, marcas de fabricante ou parafusos lidos como '0'
    busca = re.findall(r'\d{4,7}', texto)
    
    return busca[0] if busca else None

def extrair_dados_fluxo(origem):
    """
    Função principal que aplica a Estratégia em Cascata para leitura.
    Pode receber um caminho de arquivo (string) ou um frame do OpenCV (array).
    """
    try:
        # Carregamento da imagem (Suporta caracteres especiais no caminho via numpy)
        if isinstance(origem, str):
            if not os.path.exists(origem): return None, "Arquivo não encontrado"
            img_array = np.fromfile(origem, np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        else:
            frame = origem

        if frame is None:
            return "Erro", "Falha ao carregar imagem"

        h_f, w_f = frame.shape[:2]

        # --- ESTRATÉGIA EM CASCATA ---
        # Definimos recortes para focar onde os números costumam estar
        corte_focado = frame[int(h_f*0.35):int(h_f*0.75), 
                             int(w_f*0.10):int(w_f*0.90)]

        # Tentativas: Primeiro o corte central, depois a imagem cheia
        tentativas = [corte_focado, frame]

        for img_alvo in tentativas:
            # 1. Pré-processamento: Cinza e Aumento de Escala (Essencial para o Tesseract)
            cinza = cv2.cvtColor(img_alvo, cv2.COLOR_BGR2GRAY)
            cinza = cv2.resize(cinza, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

            # --- TESTE A: OTSU (Bom para iluminação uniforme) ---
            _, t1 = cv2.threshold(cinza, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            res = processar_e_ler(t1)
            if res:
                cv2.imwrite("debug_ocr_sucesso.png", t1) # Salva para conferência
                return "Identificado", res

            # --- TESTE B: ADAPTATIVO INVERTIDO (Bom para sombras/reflexos) ---
            # Ele analisa blocos de pixels, ideal para quando há lanterna envolvida
            t2 = cv2.adaptiveThreshold(cinza, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                       cv2.THRESH_BINARY_INV, 25, 11)
            res = processar_e_ler(t2)
            if res:
                cv2.imwrite("debug_ocr_sucesso.png", t2)
                return "Identificado", res

        return "Não identificado", None

    except Exception as e:
        return "Erro", str(e)

# Exemplo de uso para teste rápido:
if __name__ == "__main__":
    # status, valor = extrair_dados_fluxo("caminho_da_foto.jpg")
    # print(f"Status: {status} | Valor: {valor}")
    pass