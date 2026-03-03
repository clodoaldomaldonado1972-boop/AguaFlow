from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import os


def gerar_pdf_etiquetas_qr(lista_unidades):
    nome_pdf = "Etiquetas_QR_Vivere.pdf"
    c = canvas.Canvas(nome_pdf, pagesize=A4)
    width, height = A4

    # Configurações de layout (ajustável)
    colunas = 4
    linhas = 6
    margem_x = 1.5 * cm
    margem_y = 2 * cm
    espaco_x = 4.5 * cm
    espaco_y = 4.5 * cm
    tamanho_qr = 3.5 * cm

    x_atual = margem_x
    y_atual = height - margem_y - tamanho_qr

    cont_col = 0
    cont_lin = 0

    for unidade in lista_unidades:
        caminho_img = f"qr_codes/{unidade}.png"

        if os.path.exists(caminho_img):
            # Desenha o QR Code
            c.drawImage(caminho_img, x_atual, y_atual,
                        width=tamanho_qr, height=tamanho_qr)

            # Desenha o texto centralizado embaixo
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(x_atual + (tamanho_qr/2),
                                y_atual - 15, unidade.replace("_", " "))

            # Lógica de movimentação da "caneta" no PDF
            cont_col += 1
            x_atual += espaco_x

            if cont_col >= colunas:
                cont_col = 0
                x_atual = margem_x
                y_atual -= espaco_y
                cont_lin += 1

            # Se encher a página, cria uma nova
            if cont_lin >= linhas:
                c.showPage()
                y_atual = height - margem_y - tamanho_qr
                cont_lin = 0

    c.save()
    return nome_pdf
