import qrcode
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# --- CONFIGURAÇÕES DE LAYOUT ---
COLUNAS = 5
LINHAS = 8
NOME_CONDOMINIO = "Vivere Prudente"


def gerar_qr_codes(filtro_tipo="AMBOS"):
    """Gera o PDF de etiquetas para o condomínio."""
    nome_output = f"Etiquetas_AguaFlow_{filtro_tipo}.pdf"
    c = canvas.Canvas(nome_output, pagesize=A4)
    width, height = A4

    lista_impressao = []

    # 1. GERAÇÃO DA LISTA (Andares 16 ao 1)
    for andar in range(16, 0, -1):
        for final in range(6, 0, -1):
            unidade = f"{andar}{final}"
            if filtro_tipo in ["AGUA", "AMBOS"]:
                lista_impressao.append(
                    {"id": unidade, "tipo": "AGUA", "payload": f"{unidade}-AGUA"})
            if filtro_tipo in ["GAS", "AMBOS"]:
                lista_impressao.append(
                    {"id": unidade, "tipo": "GAS", "payload": f"{unidade}-GAS"})

    # Áreas Especiais
    if filtro_tipo in ["GAS", "AMBOS"]:
        lista_impressao.append(
            {"id": "LAZER", "tipo": "GAS", "payload": "LAZER-GAS"})
    if filtro_tipo in ["AGUA", "AMBOS"]:
        lista_impressao.append(
            {"id": "GERAL", "tipo": "AGUA", "payload": "GERAL-AGUA"})

    margem_x, margem_y = 20, 20
    w_cel = (width - 2 * margem_x) / COLUNAS
    h_cel = (height - 2 * margem_y) / LINHAS

    for i, item in enumerate(lista_impressao):
        if i > 0 and i % (COLUNAS * LINHAS) == 0:
            c.showPage()

        idx = i % (COLUNAS * LINHAS)
        col, row = idx % COLUNAS, idx // COLUNAS
        x = margem_x + (col * w_cel)
        y = height - margem_y - ((row + 1) * h_cel)

        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(item['payload'])
        qr.make(fit=True)
        img_qr = qr.make_image(fill_color="black", back_color="white")

        temp_img = f"temp_qr_{item['payload']}.png"
        img_qr.save(temp_img)

        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.rect(x, y, w_cel, h_cel, stroke=1, fill=0)

        qr_size = min(w_cel * 0.6, h_cel * 0.45)
        img_reader = ImageReader(temp_img)
        c.drawImage(img_reader, x + (w_cel - qr_size) / 2, y +
                    h_cel - qr_size - 30, width=qr_size, height=qr_size)

        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x + w_cel / 2, y + 20,
                            f"{item['id']} - {item['tipo']}")

        c.setFont("Helvetica", 7)
        c.drawCentredString(x + w_cel / 2, y + 10, NOME_CONDOMINIO)

        os.remove(temp_img)

    c.save()
    print(f"✅ Arquivo '{nome_output}' gerado com sucesso!")
    return nome_output


if __name__ == "__main__":
    gerar_qr_codes("AMBOS")
