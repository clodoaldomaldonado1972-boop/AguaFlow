import os
from datetime import datetime
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
# Import do gerador de QR que agora está na pasta utils
from utils import gerador_qr[cite: 14]

# --- GERAÇÃO DE ETIQUETAS QR ---


def gerar_pdf_etiquetas(lista_unidades):
    # Salva na pasta 'storage' para manter a raiz limpa
    caminho_pdf = os.path.join("storage", "Etiquetas_QR_Vivere.pdf")
    c = canvas.Canvas(caminho_pdf, pagesize=A4)
    width, height = A4

    colunas, linhas = 3, 5
    margem_x, margem_y = 1.5 * cm, 2.0 * cm
    espaco_x, espaco_y = 6.2 * cm, 5.2 * cm
    tamanho_qr = 3.5 * cm

    x_atual, y_atual = margem_x, height - margem_y - tamanho_qr
    cont_col = cont_lin = 0

    for unidade in lista_unidades:
        # Busca as imagens na pasta qrcodes da raiz
        caminho_img = f"qrcodes/{unidade}.png"[cite: 14]

        if not os.path.exists(caminho_img):
            try:
                gerador_qr.gerar_imagem_unidade(unidade)
            except:
                pass

        if os.path.exists(caminho_img):
            c.drawImage(caminho_img, x_atual + 1.2*cm, y_atual,
                        width=tamanho_qr, height=tamanho_qr)[cite: 14]

            centro_x = x_atual + 1.2*cm + (tamanho_qr/2)
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(centro_x, y_atual - 15, "VIVERE PRUDENTE")
            c.setFont("Helvetica", 9)
            c.drawCentredString(centro_x, y_atual - 28,
                                f"APTO: {unidade}")[cite: 14]

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
    return caminho_pdf

# --- GERAÇÃO DO RELATÓRIO MENSAL ---


def gerar_relatorio_consumo(dados):
    # Organiza dentro da pasta 'relatorios' que já existe na sua estrutura
    pasta_nome = datetime.now().strftime("relatorios/Relatorios_%Y_%m")
    if not os.path.exists(pasta_nome):
        os.makedirs(pasta_nome)[cite: 14]

    timestamp = datetime.now().strftime("%d_%H%M%S")
    nome_arquivo = os.path.join(
        pasta_nome, f"Relatorio_Vivere_{timestamp}.pdf")[cite: 14]

    c = canvas.Canvas(nome_arquivo, pagesize=letter)
    width, height = letter

    def cabecalho(canvas_obj, y_p):
        canvas_obj.setFont("Helvetica-Bold", 14)
        canvas_obj.drawCentredString(
            width/2, y_p, "RELATÓRIO DE CONSUMO - VIVERE PRUDENTE")[cite: 14]

        y_tab = y_p - 45
        canvas_obj.setFont("Helvetica-Bold", 9)
        canvas_obj.drawString(50, y_tab, "UNID")
        canvas_obj.drawString(100, y_tab, "LEIT. ANT (DATA)")
        canvas_obj.drawString(250, y_tab, "LEIT. ATU (DATA)")
        canvas_obj.drawString(450, y_tab, "CONSUMO")
        canvas_obj.line(50, y_tab - 5, 550, y_tab - 5)
        return y_tab - 20[cite: 14]

    y = cabecalho(c, 750)

    for r in dados:
        unid = str(r[0])
        try:
            atu = float(r[1]) if r[1] is not None else 0.0
            ant = float(r[2]) if r[2] is not None else 0.0
        except:
            atu, ant = 0.0, 0.0[cite: 14]

        dt_atu = r[3] if r[3] else "--/--/--"
        dt_ant = r[4] if r[4] else "--/--/--"

        if y < 50:
            c.showPage()
            y = cabecalho(c, 750)[cite: 14]

        c.setFont("Helvetica", 9)
        c.drawString(50, y, unid)
        c.drawString(100, y, f"{ant:8.2f} ({dt_ant[:10]})")
        c.drawString(250, y, f"{atu:8.2f} ({dt_atu[:10]})")

        consumo = max(0, atu - ant)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(450, y, f"{consumo:8.2f} m³")[cite: 14]
        y -= 18

    c.save()
    # Abre o PDF automaticamente no Windows se necessário
    if os.name == 'nt' and os.path.exists(nome_arquivo):
        os.startfile(nome_arquivo)[cite: 14]

    return nome_arquivo
