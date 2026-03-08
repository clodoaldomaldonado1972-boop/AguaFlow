import qrcode
import os


def gerar_qr_vivere():
    # PADRONIZAÇÃO: Usando "qrcodes" (sem underline) para bater com o utils.py
    pasta = "qrcodes"
    if not os.path.exists(pasta):
        os.makedirs(pasta)

    # Lista base: Áreas comuns
    unidades = ["Hidrometro_Geral", "Area_de_Lazer"]

    # Gera os 16 andares (do 16 ao 1)
    for andar in range(16, 0, -1):
        for apto in range(1, 7):
            # PADRONIZAÇÃO: Salvando apenas o número (ex: 161)
            # Se o seu banco usa "Apto_161", volte para: f"Apto_{andar}{apto}"
            unidades.append(f"{andar}{apto:02}")

    print(f"🚀 Iniciando geração de {len(unidades)} QR Codes...")

    for unidade in unidades:
        # Configuração técnica do QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4
        )
        qr.add_data(unidade)
        qr.make(fit=True)

        # Cria a imagem
        img = qr.make_image(fill_color="black", back_color="white")

        # Salva o arquivo na pasta correta
        caminho = os.path.join(pasta, f"{unidade}.png")
        img.save(caminho)

    print(f"✅ Sucesso! {len(unidades)} arquivos salvos em '{pasta}/'.")


if __name__ == "__main__":
    gerar_qr_vivere()
