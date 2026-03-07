import os
import qrcode
import flet as ft
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
import database as db

# --- 1. GERAÇÃO DE ETIQUETAS E QR CODES ---


def gerar_qr_imagem(unidade):
    """Gera uma imagem PNG do QR Code para uma unidade específica."""
    if not os.path.exists("qrcodes"):
        os.makedirs("qrcodes")

    caminho = f"qrcodes/{str(unidade)}.png"
    if not os.path.exists(caminho):
        # O conteúdo do QR Code é apenas o número da unidade
        img = qrcode.make(str(unidade))
        img.save(caminho)
    return caminho


def gerar_pdf_etiquetas_qr(lista_unidades, nome_pdf="Etiquetas_A4.pdf"):
    """Cria um PDF formatado com vários QR Codes para impressão."""
    c = canvas.Canvas(nome_pdf, pagesize=A4)
    width, height = A4
    x, y = 1.5*cm, height - 4*cm  # Margens iniciais

    for unidade in lista_unidades:
        img = gerar_qr_imagem(unidade)
        # Desenha o QR Code
        c.drawImage(img, x, y, width=3.5*cm, height=3.5*cm)
        c.setFont("Helvetica-Bold", 10)
        # Escreve o número da unidade abaixo do código
        c.drawCentredString(x + 1.75*cm, y - 0.4*cm, f"UNIDADE: {unidade}")

        # Lógica de colunas (3 por linha)
        x += 4.8*cm
        if x > width - 4*cm:
            x = 1.5*cm
            y -= 5*cm

        # Nova página se chegar ao fim
        if y < 2*cm:
            c.showPage()
            y = height - 4*cm

    c.save()
    os.startfile(nome_pdf)  # Abre o arquivo no Windows
    return nome_pdf

# --- 2. RELATÓRIO DE LEITURAS (Onde estava o erro) ---


def gerar_relatorio_leituras_pdf(dados, nome_pdf="Relatorio_Mensal.pdf"):
    """Gera o relatório financeiro/consumo corrigindo valores nulos."""
    c = canvas.Canvas(nome_pdf, pagesize=A4)
    width, height = A4
    y = height - 2*cm

    # Cabeçalho
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, y, "ÁguaFlow - Relatório de Leituras Mensal")
    y -= 1.5*cm

    # Títulos das Colunas
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2*cm, y, "Unidade")
    c.drawString(5*cm, y, "Anterior")
    c.drawString(9*cm, y, "Atual")
    c.drawString(13*cm, y, "Consumo")
    y -= 0.6*cm

    c.setFont("Helvetica", 10)
    for row in dados:
        # Extração dos dados do banco (ajuste os índices conforme seu SELECT)
        unid = row[1]
        ant = row[2]
        atu = row[3]
        cons = row[4]

        # --- PROTEÇÃO CONTRA NONETYPE (O SEGREDO) ---
        # Se o valor for None (não lido), usamos 0.00 para não quebrar o PDF
        txt_ant = f"{ant:.2f}" if ant is not None else "0.00"
        txt_atu = f"{atu:.2f}" if atu is not None else "0.00"
        txt_cons = f"{cons:.2f}" if cons is not None else "0.00"

        # Desenha a linha no PDF
        c.drawString(2*cm, y, str(unid))
        c.drawString(5*cm, y, txt_ant)
        c.drawString(9*cm, y, txt_atu)
        c.drawString(13*cm, y, txt_cons)

        y -= 0.6*cm
        # Controle de quebra de página
        if y < 2*cm:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - 2*cm

    c.save()
    os.startfile(nome_pdf)
    return nome_pdf

# --- 3. INTERFACE FLET ---


def montar_tela_relatorios(page, voltar):
    """Cria a interface visual para o usuário interagir com os relatórios."""

    def acao_gerar_pdf(e):
        dados = db.buscar_todas_leituras()
        if dados:
            gerar_relatorio_leituras_pdf(dados)
            page.snack_bar = ft.SnackBar(
                ft.Text("PDF de Leituras Gerado!"), open=True)
        else:
            page.snack_bar = ft.SnackBar(
                ft.Text("Banco de dados vazio!"), open=True)
        page.update()

    def acao_gerar_etiquetas(e):
        unidades = [u[1] for u in db.buscar_todas_leituras()]
        if unidades:
            gerar_pdf_etiquetas_qr(unidades)
            page.snack_bar = ft.SnackBar(
                ft.Text("Etiquetas Geradas!"), open=True)
        page.update()

    return ft.Container(
        expand=True, bgcolor="#1A1C1E", padding=30,
        content=ft.Column([
            ft.Text("Painel de Relatórios", size=28,
                    color="white", weight="bold"),
            ft.Divider(color="white10"),
            ft.ElevatedButton("GERAR PDF DE LEITURAS",
                              icon=ft.Icons.PICTURE_AS_PDF,
                              on_click=acao_gerar_pdf, width=300),
            ft.ElevatedButton("GERAR ETIQUETAS QR",
                              icon=ft.Icons.QR_CODE,
                              on_click=acao_gerar_etiquetas, width=300),
            ft.Container(height=20),
            ft.TextButton("Voltar ao Menu", on_click=lambda _: voltar())
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )
