import os
from datetime import datetime
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from . import gerador_qr

# --- GERAÇÃO DE ETIQUETAS QR ---


def gerar_pdf_etiquetas(lista_unidades):
    nome_pdf = "Etiquetas_QR_Vivere.pdf"
    c = canvas.Canvas(nome_pdf, pagesize=A4)
    width, height = A4

    # Grade técnica para evitar sobreposição
    colunas, linhas = 3, 5
    margem_x, margem_y = 1.5 * cm, 2.0 * cm
    # Espaçamento calculado para preencher a folha A4
    espaco_x, espaco_y = 6.2 * cm, 5.2 * cm
    tamanho_qr = 3.5 * cm

    x_atual, y_atual = margem_x, height - margem_y - tamanho_qr
    cont_col = cont_lin = 0

    for unidade in lista_unidades:
        caminho_img = f"qrcodes/{unidade}.png"

        if not os.path.exists(caminho_img):
            # Tenta gerar se não existir
            try:
                gerador_qr.gerar_imagem_unidade(unidade)
            except:
                pass

        if os.path.exists(caminho_img):
            # Centraliza o QR dentro do espaço da "célula"
            c.drawImage(caminho_img, x_atual + 1.2*cm, y_atual,
                        width=tamanho_qr, height=tamanho_qr)

            # Identificação centralizada abaixo do QR
            centro_x = x_atual + 1.2*cm + (tamanho_qr/2)
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(centro_x, y_atual - 15, "VIVERE PRUDENTE")
            c.setFont("Helvetica", 9)
            c.drawCentredString(centro_x, y_atual - 28, f"APTO: {unidade}")

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

# --- GERAÇÃO DO RELATÓRIO MENSAL ORGANIZADO ---


def gerar_relatorio_consumo(dados):
    # Modularização: Criando pasta por mês
    pasta_nome = datetime.now().strftime("Relatorios_%Y_%m")
    if not os.path.exists(pasta_nome):
        os.makedirs(pasta_nome)

    timestamp = datetime.now().strftime("%d_%H%M%S")
    nome_arquivo = os.path.join(
        pasta_nome, f"Relatorio_Vivere_{timestamp}.pdf")

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
        canvas_obj.drawString(
            250, y_tab, "LEIT. ATU (DATA)")  # Ajustado espaço
        canvas_obj.drawString(450, y_tab, "CONSUMO")
        canvas_obj.line(50, y_tab - 5, 550, y_tab - 5)
        return y_tab - 20

    y = cabecalho(c, 750)

    for r in dados:
        # Garante que temos valores numéricos para o cálculo
        unid = str(r[0])
        try:
            atu = float(r[1]) if r[1] is not None else 0.0
            ant = float(r[2]) if r[2] is not None else 0.0
        except:
            atu, ant = 0.0, 0.0

        dt_atu = r[3] if r[3] else "--/--/--"
        dt_ant = r[4] if r[4] else "--/--/--"

        # Limite de página
        if y < 50:
            c.showPage()
            y = cabecalho(c, 750)

        c.setFont("Helvetica", 9)
        c.drawString(50, y, unid)

        # Formatação ajustada para não encavalar se o número for grande
        # Pegamos apenas os 10 primeiros caracteres da data (DD/MM/AAAA)
        c.drawString(100, y, f"{ant:8.2f} ({dt_ant[:10]})")
        c.drawString(250, y, f"{atu:8.2f} ({dt_atu[:10]})")

        consumo = max(0, atu - ant)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(450, y, f"{consumo:8.2f} m³")
        y -= 18

    c.save()
    if os.name == 'nt':
        os.startfile(nome_arquivo)
    return nome_arquivo
