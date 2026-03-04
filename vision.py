import cv2
from pyzbar.pyzbar import decode


def escanear_qr():
    """Abre a câmera e retorna o conteúdo do QR Code quando encontrado."""
    cap = cv2.VideoCapture(0)  # 0 é a câmera padrão do seu PC/Notebook

    print("Buscando QR Code... Pressione 'q' para sair.")

    resultado = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Tenta encontrar e decodificar QR Codes no frame atual
        for code in decode(frame):
            resultado = code.data.decode('utf-8')
            print(f"QR Code detectado: {resultado}")

            # Desenha um retângulo ao redor do QR Code (opcional, para feedback visual)
            cv2.rectangle(frame, (code.rect.left, code.rect.top),
                          (code.rect.left + code.rect.width,
                           code.rect.top + code.rect.height),
                          (0, 255, 0), 3)

        cv2.imshow('AguaFlow Scanner - Posicione o QR Code', frame)

        # Se encontrar o código ou apertar 'q', sai do loop
        if resultado or cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return resultado


if __name__ == "__main__":
    # Teste simples do scanner
    codigo = escanear_qr()
    if codigo:
        print(f"Sucesso! Conteúdo: {codigo}")
