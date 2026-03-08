import os
from datetime import datetime
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
import gerador_qr

# --- GERAÇÃO DE ETIQUETAS QR ---


def gerar_pdf_etiquetas(lista_unidades):
    nome_pdf = "Etiquetas_QR_Vivere.pdf"
    c = canvas.Canvas(nome_pdf, pagesize=A4)
    width, height = A4

    # Grade de segurança para não encavalar
    colunas, linhas = 3, 5
    margem_x, margem_y = 2.0 * cm, 2.5 * cm
    espaco_x, espaco_y = 6.5 * cm, 5.0 * cm
    tamanho_qr = 3.0 * cm

    x_atual, y_atual = margem_x, height - margem_y - tamanho_qr
    cont_col = cont_lin = 0

    for unidade in lista_unidades:
        caminho_img = f"qrcodes/{unidade}.png"

        # Garante que a imagem existe
        if not os.path.exists(caminho_img):
            gerador_qr.gerar_imagem_unidade(unidade)

        if os.path.exists(caminho_img):
            c.drawImage(caminho_img, x_atual, y_atual,
                        width=tamanho_qr, height=tamanho_qr)

            # Identificação (Nome do Condomínio e Unidade)
            c.setFont("Helvetica-Bold", 11)
            c.drawCentredString(x_atual + (tamanho_qr/2),
                                y_atual - 18, "VIVERE PRUDENTE")
            c.setFont("Helvetica", 10)
            c.drawCentredString(x_atual + (tamanho_qr/2),
                                y_atual - 32, f"APTO: {unidade}")

            cont_col += 1
            x_atual += espaco_x
            if cont_col >= colunas:
                cont_col, x_atual = 0, margem_x
                y_atual -= espaco_y
                cont_lin += 1
            if cont_lin >= linhas:
                c.showPage()
                y_atual = height - margem_y - tamanho_qr
                cont_lin = cont_col = 0
                x_atual = margem_x
    c.save()
    return nome_pdf

# --- GERAÇÃO DO RELATÓRIO MENSAL COM DATAS ---


def gerar_relatorio_consumo(dados):
    nome_arquivo = "relatorio_mensal.pdf"
    c = canvas.Canvas(nome_arquivo, pagesize=letter)
    width, height = letter

    def cabecalho(canvas_obj, y_p):
        canvas_obj.setFont("Helvetica-Bold", 14)
        canvas_obj.drawCentredString(
            width/2, y_p, "RELATÓRIO DE CONSUMO - VIVERE PRUDENTE")
        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.drawCentredString(
            width/2, y_p - 15, f"Extraído em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

        y_tab = y_p - 45
        canvas_obj.setFont("Helvetica-Bold", 9)
        canvas_obj.drawString(50, y_tab, "UNID")
        canvas_obj.drawString(100, y_tab, "LEIT. ANT (DATA)")
        canvas_obj.drawString(260, y_tab, "LEIT. ATU (DATA)")
        canvas_obj.drawString(420, y_tab, "CONSUMO")
        canvas_obj.line(50, y_tab - 5, 550, y_tab - 5)
        return y_tab - 20

    y = cabecalho(c, 750)
    # Dentro de gerador_pdf.py -> def gerar_relatorio_consumo(dados):

    for r in dados:
        # r[0]=unid, r[1]=atual, r[2]=anterior, r[3]=data_atual, r[4]=data_anterior
        unid = str(r[0])
        atu = r[1] if r[1] else 0
        ant = r[2] if r[2] else 0
        dt_atu = r[3] if r[3] else "--/--/--"  # Se vier vazio, coloca traços
        dt_ant = r[4] if r[4] else "--/--/--"

        c.setFont("Helvetica", 9)
        c.drawString(50, y, unid)

        # Aqui imprimimos o valor e a data entre parênteses
        c.drawString(100, y, f"{ant:>7} ({dt_ant})")
        c.drawString(260, y, f"{atu:>7} ({dt_atu})")

        consumo = max(0, atu - ant)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(420, y, f"{consumo:>7} m³")
        y -= 18

    c.save()
    return nome_arquivo
