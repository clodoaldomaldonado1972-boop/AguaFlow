import time


def escanear_qr():
    """SIMULADOR DE CÂMERA"""
    print("--- [SIMULADOR] Abrindo visor da câmera... ---")
    time.sleep(1.5)
    print("--- [SIMULADOR] QR Code lido com sucesso! ---")

    # Retorna "101" para testar a lógica do app
    return "101"


if __name__ == "__main__":
    res = escanear_qr()
    print(f"Resultado do Simulador: {res}")
