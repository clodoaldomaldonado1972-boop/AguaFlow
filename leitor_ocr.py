import cv2
import pytesseract
import re

# Se o Tesseract não estiver no PATH do Windows, descomente a linha abaixo e aponte o caminho:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def capturar_e_ler_hidrometro():
    """Abre a câmera, captura um frame e tenta ler os números."""
    cap = cv2.VideoCapture(0)  # 0 para webcam ou câmera principal do celular

    leitura_final = ""

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 1. Processamento da imagem (Cinza e Contraste)
        cinza = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, threshold = cv2.threshold(cinza, 150, 255, cv2.THRESH_BINARY)

        # 2. Define a área de leitura (um retângulo no centro da tela)
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (w//4, h//3), (3*w//4, 2*h//3), (0, 255, 0), 2)

        # Exibe a câmera (No computador)
        cv2.imshow(
            "Aponte para o visor do Hidrometro - Pressione 'S' para Capturar", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):  # Pressiona 'S' para ler
            # Corta a imagem apenas para a área do retângulo
            recorte = threshold[h//3:2*h//3, w//4:3*w//4]
            # OCR: Configurado para ler apenas dígitos (--psm 6 ou 7)
            texto = pytesseract.image_to_string(
                recorte, config='--psm 7 digits')
            # Limpa o texto (pega apenas números)
            leitura_final = "".join(re.findall(r'\d+', texto))
            break
        elif key == 27:  # ESC para sair
            break

    cap.release()
    cv2.destroyAllWindows()
    return leitura_final
