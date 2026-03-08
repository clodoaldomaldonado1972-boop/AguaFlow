import qrcode
import os
from PIL import Image, ImageDraw, ImageFont


def gerar_imagem_unidade(unidade, condominio="VIVERE PRUDENTE"):
    pasta = "qrcodes"
    if not os.path.exists(pasta):
        os.makedirs(pasta)

    # 1. CRIAR O QR CODE PURO
    qr = qrcode.QRCode(
        version=1,
        # Alta correção para permitir texto
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(str(unidade))
    qr.make(fit=True)
    img_qr = qr.make_image(
        fill_color="black", back_color="white").convert('RGB')

    # 2. ADICIONAR ESPAÇO PARA O TEXTO (Aumenta a imagem para baixo)
    largura, altura = img_qr.size
    nova_altura = altura + 80  # Espaço extra de 80 pixels para o texto
    img_final = Image.new('RGB', (largura, nova_altura), 'white')
    img_final.paste(img_qr, (0, 0))

    # 3. ESCREVER O NOME E A UNIDADE NA IMAGEM
    draw = ImageDraw.Draw(img_final)

    # Tenta carregar uma fonte, se não tiver usa a padrão
    try:
        font_titulo = ImageFont.truetype("arialbd.ttf", 25)
        font_unid = ImageFont.truetype("arial.ttf", 22)
    except:
        font_titulo = font_unid = ImageFont.load_default()

    # Centralizar e desenhar o texto
    texto_condo = condominio
    texto_unid = f"APTO: {unidade}"

    # Calcula posições centrais
    w_condo = draw.textlength(texto_condo, font=font_titulo)
    w_unid = draw.textlength(texto_unid, font=font_unid)

    draw.text(((largura - w_condo) / 2, altura - 5),
              texto_condo, fill="black", font=font_titulo)
    draw.text(((largura - w_unid) / 2, altura + 30),
              texto_unid, fill="black", font=font_unid)

    # 4. SALVAR
    caminho = os.path.join(pasta, f"{unidade}.png")
    img_final.save(caminho)
    return caminho


def gerar_todos_vivere():
    print("🚀 Gerando imagens com Identificação Integrada...")
    # Áreas comuns
    comuns = ["Geral", "Lazer"]
    for item in comuns:
        gerar_imagem_unidade(item)

    # Apartamentos (16 andares)
    for andar in range(16, 0, -1):
        for apto in range(1, 7):
            unidade = f"{andar}{apto:02}"
            gerar_imagem_unidade(unidade)
    print("✅ Todas as imagens foram criadas na pasta /qrcodes")


if __name__ == "__main__":
    gerar_todos_vivere()
