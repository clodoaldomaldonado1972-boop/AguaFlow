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
        # --psm 6: Assume que a imagem é um único bloco de texto (mais flexível para fotos).
        # --oem 3: Usa o motor de inteligência artificial mais moderno do Tesseract.
        # whitelist: Diz ao robô para ignorar letras e focar apenas nos números 0-9.
        config_ocr = '--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789'
        leitura = pytesseract.image_to_string(binaria, config=config_ocr)

        # Retorna o texto limpo (sem espaços extras nas pontas)
        return leitura.strip()

    except Exception as e:
        print(f"Erro técnico no processamento do OCR: {e}")
        return None
    finally:
        # LIMPEZA DE MEMÓRIA RAM
        # Garante que as imagens pesadas sejam apagadas da memória após o uso.
        if frame_res is not None:
            del frame_res
        if binaria is not None:
            del binaria
        gc.collect()
