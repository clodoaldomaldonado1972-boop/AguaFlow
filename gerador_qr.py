import qrcode
import os


def garantir_pasta_existente(pasta="qrcodes"):
    """Cria a pasta onde as imagens serão salvas, se não existir."""
    if not os.path.exists(pasta):
        os.makedirs(pasta)
        print(f"✅ Pasta '{pasta}' criada.")


def gerar_imagem_unidade(unidade, pasta="qrcodes"):
    """Gera o arquivo PNG de um único QR Code."""
    garantir_pasta_existente(pasta)

    # Configuração técnica para leitura fácil em locais escuros
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,  # Nível Médio de correção
        box_size=10,
        border=4,
    )

    qr.add_data(str(unidade))
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Define o nome do arquivo (ex: qrcodes/161.png)
    caminho = os.path.join(pasta, f"{unidade}.png")
    img.save(caminho)
    return caminho


def gerar_todos_vivere():
    """Gera a carga total de QR Codes do condomínio de uma vez só."""
    garantir_pasta_existente()

    # 1. Áreas Comuns
    lista_unidades = ["Hidrometro_Geral", "Area_de_Lazer"]

    # 2. Apartamentos (16 andares, 6 por andar)
    # Usamos o :02 para o apto 1 virar 01 (ex: 1601 em vez de 161 se preferir padrão 4 dígitos)
    # Se o seu banco usa 3 dígitos (161), use: f"{andar}{apto}"
    for andar in range(16, 0, -1):
        for apto in range(1, 7):
            unidade = f"{andar}{apto:02}"
            lista_unidades.append(unidade)

    print(f"🚀 Gerando {len(lista_unidades)} imagens...")

    for uni in lista_unidades:
        gerar_imagem_unidade(uni)

    print("✅ Processo concluído! Todas as imagens estão na pasta /qrcodes.")


if __name__ == "__main__":
    # Se você rodar este arquivo diretamente (python gerador_qr.py),
    # ele gera todos os 98 códigos de uma vez.
    gerar_todos_vivere()
