import cv2
import pytesseract
import numpy as np
import gc
import os

# Configuração do caminho do executável do Tesseract (Motor do OCR)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def extrair_dados_fluxo(origem):
    """
    Função principal para transformar a imagem do hidrômetro em números digitais.
    """
    frame_res = None
    cinza = None
    suave = None
    binaria = None

    try:
        # 1. CARREGAMENTO ROBUSTO
        # Usamos o numpy (np.fromfile) porque o OpenCV padrão falha com acentos (ex: ÁguaFlow)
        if isinstance(origem, str):
            if not os.path.exists(origem):
                return None
            # Lê os bytes brutos do arquivo e decodifica para o formato de imagem
            img_array = np.fromfile(origem, np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        else:
            frame = origem

        # Validação: Se a imagem estiver corrompida ou vazia, interrompe aqui
        if frame is None:
            print("Erro: Não foi possível carregar a imagem.")
            return None

        # 2. REDIMENSIONAMENTO INTELIGENTE
        # O Tesseract trabalha melhor com imagens de tamanho padrão (800px de largura).
        # Mantemos a proporção da altura para não deformar os números.
        h_orig, w_orig = frame.shape[:2]
        proporcao = 800 / w_orig
        frame_res = cv2.resize(
            frame, (800, int(h_orig * proporcao)), interpolation=cv2.INTER_CUBIC)

        # 3. FILTRAGEM DE RUÍDO (LIMPEZA)
        # Primeiro, convertemos para tons de cinza para simplificar a análise.
        cinza = cv2.cvtColor(frame_res, cv2.COLOR_BGR2GRAY)

        # O Filtro Bilateral remove a "sujeira" da foto (ruído), mas mantém as bordas
        # dos números nítidas. Isso evita que os números fiquem borrados.
        suave = cv2.bilateralFilter(cinza, 9, 75, 75)

        # 4. BINARIZAÇÃO (O "RAIO-X")
        # Transforma tudo em Preto (número) e Branco (fundo).
        # O algoritmo OTSU calcula automaticamente o melhor contraste para a foto.
        _, binaria = cv2.threshold(
            suave, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # 5. SALVAMENTO DE DIAGNÓSTICO
        # Cria a "visao_do_robo.png". Se o resultado for ❌, abra este arquivo para ver
        # se o robô está conseguindo enxergar os números pretos no fundo branco.
        cv2.imwrite("visao_do_robo.png", binaria)

        # 6. MOTOR DE RECONHECIMENTO (OCR)
        config_ocr = '--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789'
        leitura_bruta = pytesseract.image_to_string(binaria, config=config_ocr)

        # Filtra apenas os números
        numeros = "".join(filter(str.isdigit, leitura_bruta))

        # 7. REGRA DE NEGÓCIO: Visor de 6 campos com 2 decimais
        qtd = len(numeros)

        if 3 <= qtd <= 6:
            # Se temos pelo menos 3 dígitos, podemos formatar as 2 últimas casas
            # Ex: "123456" vira "1234.56" | "123" vira "1.23"
            inteiros = numeros[:-2]
            decimais = numeros[-2:]

            # Se a leitura for muito curta (ex: 23), adiciona o 0 na frente: "0.23"
            if not inteiros:
                inteiros = "0"

            resultado_final = f"{inteiros}.{decimais}"
            return resultado_final

        elif qtd > 6:
            print(
                f"⚠️ Ignorado: {qtd} dígitos detectados (Provável número de série).")
            return None

        else:
            # Se tiver apenas 1 ou 2 dígitos, é ruído visual
            return None
