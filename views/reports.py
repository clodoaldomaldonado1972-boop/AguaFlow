import os
import qrcode
from datetime import datetime
import flet as ft
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
import database as db

# =============================================================================
# 1. MÓDULO DE INFRAESTRUTURA (Arquivos e Pastas)
# =============================================================================


def preparar_caminho_pdf():
    """Cria a pasta do mês e define o nome do arquivo com timestamp."""
    pasta_mensal = datetime.now().strftime("Relatorios_%Y_%m")
    if not os.path.exists(pasta_mensal):
        os.makedirs(pasta_mensal)
    timestamp = datetime.now().strftime("%d_%H%M%S")
    return os.path.join(pasta_mensal, f"Relatorio_Vivere_{timestamp}.pdf")


def buscar_imagem_qr(unidade):
    """Gera o QR Code da unidade caso ele ainda não exista."""
    if not os.path.exists("qrcodes"):
        os.makedirs("qrcodes")
    caminho = f"qrcodes/{str(unidade)}.png"
    if not os.path.exists(caminho):
        img = qrcode.make(str(unidade))
        img.save(caminho)
    return caminho

# =============================================================================
# 2. MÓDULO DE FORMATAÇÃO VISUAL (Design do PDF)
# =============================================================================


def desenhar_cabecalho(canvas_obj, y_pos):
    """Desenha o título e o cabeçalho da tabela no PDF."""
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    canvas_obj.setFont("Helvetica-Bold", 14)
    canvas_obj.drawString(
        1.5*cm, y_pos, f"AguaFlow - Vivere Prudente - {data_hoje}")

    y_pos -= 0.8*cm
    canvas_obj.setFont("Helvetica-Bold", 9)
    canvas_obj.drawString(1.5*cm, y_pos, "Unidade")
    canvas_obj.drawString(4.0*cm, y_pos, "Leitura Anterior")
    canvas_obj.drawString(10.0*cm, y_pos, "Leitura Atual")
    canvas_obj.drawString(16.0*cm, y_pos, "Consumo")

    canvas_obj.line(1.5*cm, y_pos - 0.2*cm, 19.5*cm, y_pos - 0.2*cm)
    return y_pos - 0.6*cm

# =============================================================================
# 3. MÓDULO DE PROCESSAMENTO (Orquestração de Dados)
# =============================================================================


def gerar_pdf_etiquetas(lista_unidades):
    """Gera uma folha A4 com etiquetas QR Code para colagem nos hidrômetros."""
    nome_pdf = "Etiquetas_QR_Vivere.pdf"
    c = canvas.Canvas(nome_pdf, pagesize=A4)
    width, height = A4
    colunas, linhas = 3, 5
    margem_x, margem_y = 1.5 * cm, 2.0 * cm
    espaco_x, espaco_y = 6.2 * cm, 5.2 * cm
    tamanho_qr = 3.5 * cm
    x, y = margem_x, height - margem_y - tamanho_qr
    cont_col = 0

    for unidade in lista_unidades:
        img_path = buscar_imagem_qr(unidade)
        c.drawImage(img_path, x + 1.2*cm, y,
                    width=tamanho_qr, height=tamanho_qr)
        centro_x = x + 1.2*cm + (tamanho_qr/2)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(centro_x, y - 15, "AGUAFLOW")
        c.setFont("Helvetica", 9)
        c.drawCentredString(centro_x, y - 28, f"APTO: {unidade}")

        cont_col += 1
        x += espaco_x
        if cont_col >= colunas:
            cont_col, x = 0, margem_x
            y -= espaco_y
        if y < 2*cm:
            c.showPage()
            y = height - margem_y - tamanho_qr
            x = margem_x
            cont_col = 0
    c.save()
    if os.name == 'nt':
        os.startfile(nome_pdf)
    return nome_pdf


def gerar_relatorio_consumo(dados):
    """Cria o relatório consolidado de consumo mensal."""
    caminho_pdf = preparar_caminho_pdf()
    c = canvas.Canvas(caminho_pdf, pagesize=A4)
    width, height = A4
    y = desenhar_cabecalho(c, height - 2*cm)

    soma_total = 0
    cont_unidades = 0

    for row in dados:
        unid = str(row[0])
        atu = float(row[1]) if row[1] is not None else 0.0
        ant = float(row[2]) if row[2] is not None else 0.0
        data_atu = row[3][:10] if row[3] else "---"

        consumo = max(0, atu - ant)
        soma_total += consumo
        if row[1] is not None and row[1] > 0:
            cont_unidades += 1

        # Lógica visual: Se for 0.0, destaca que não houve leitura (Esquecido/Vazio)
        c.setFont("Helvetica", 9)
        if atu == 0:
            c.setFillColorRGB(0.7, 0, 0)  # Texto em vermelho para valor zero
        else:
            c.setFillColorRGB(0, 0, 0)

        c.drawString(1.5*cm, y, unid)
        c.drawString(4.0*cm, y, f"{ant:8.2f}")
        c.drawString(10.0*cm, y, f"{atu:8.2f} ({data_atu})")

        c.setFont("Helvetica-Bold", 9)
        c.drawString(16.0*cm, y, f"{consumo:8.2f} m³")

        y -= 0.5*cm
        # Reseta cor para o próximo
        c.setFillColorRGB(0, 0, 0)

        if y < 2.5*cm:
            c.showPage()
            y = desenhar_cabecalho(c, height - 2*cm)

    # Rodapé com Totais
    y -= 0.5*cm
    c.line(1.5*cm, y, 19.5*cm, y)
    c.setFont("Helvetica-Bold", 10)
    media = soma_total / cont_unidades if cont_unidades > 0 else 0
    c.drawString(1.5*cm, y - 0.7*cm, f"TOTAL CONSUMO: {soma_total:.2f} m³")
    c.drawString(10.0*cm, y - 0.7*cm, f"MÉDIA POR UNIDADE: {media:.2f} m³")

    c.save()
    if os.name == 'nt':
        os.startfile(caminho_pdf)
    return caminho_pdf

# =============================================================================
# 4. MÓDULO DE INTERFACE (Flet UI)
# =============================================================================


def montar_tela_relatorios(page, voltar):
    def btn_gerar_leitura(e):
        leituras = db.buscar_todas_leituras()
        if leituras:
            gerar_relatorio_consumo(leituras)
            page.snack_bar = ft.SnackBar(
                ft.Text("Relatório PDF criado!"), open=True)
            page.update()

    def btn_gerar_etiquetas(e):
        leituras = db.buscar_todas_leituras()
        unidades = [str(u[0]) for u in leituras]
        if unidades:
            gerar_pdf_etiquetas(unidades)
            page.snack_bar = ft.SnackBar(
                ft.Text("Etiquetas QR geradas!"), open=True)
            page.update()

    return ft.Container(
        expand=True, bgcolor="#1A1C1E", padding=30,
        content=ft.Column(
            controls=[
                ft.Icon(ft.Icons.ASSESSMENT, color="blue", size=50),
                ft.Text("Painel de Relatórios", size=28,
                        color="white", weight="bold"),
                ft.Divider(color="white10"),
                ft.Container(height=20),
                ft.FilledButton(content=ft.Text("GERAR RELATÓRIO MENSAL"), icon=ft.Icons.PICTURE_AS_PDF,
                                on_click=btn_gerar_leitura, width=350, height=50),
                ft.FilledButton(content=ft.Text("GERAR ETIQUETAS QR"), icon=ft.Icons.QR_CODE,
                                on_click=btn_gerar_etiquetas, width=350, height=50),
                ft.TextButton("Sair", on_click=lambda _: voltar(),
                              style=ft.ButtonStyle(color="white70"))
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        )
    )
