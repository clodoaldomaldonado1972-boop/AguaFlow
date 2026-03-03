import qrcode
import os


def gerar_qr_vivere():
    # Cria a pasta para salvar os códigos se ela não existir
    if not os.path.exists("qr_codes"):
        os.makedirs("qr_codes")

    # Lista base: Áreas comuns
    unidades = ["Hidrometro_Geral", "Area_de_Lazer"]

    # Gera os 16 andares (6 aptos por andar)
    for andar in range(16, 0, -1):
        for apto in range(1, 7):
            unidades.append(f"Apto_{andar}{apto}")

    print(f"Gerando {len(unidades)} QR Codes...")

    for unidade in unidades:
        # Cria o conteúdo do QR Code (Texto que a câmera vai ler)
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(unidade)
        qr.make(fit=True)

        # Transforma em imagem
        img = qr.make_image(fill_color="black", back_color="white")

        # Salva o arquivo com o nome da unidade
        img.save(f"qr_codes/{unidade}.png")

    print("✅ Todos os QR Codes foram salvos na pasta 'qr_codes'!")


if __name__ == "__main__":
    gerar_qr_vivere()
