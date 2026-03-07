from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
import qrcode
import os
import flet as ft
import database as db  # Certifique-se de que o arquivo se chama database.py

# --- FUNÇÕES DE GERAÇÃO (LÓGICA) ---


def gerar_qr_imagem(unidade):
    if not os.path.exists("qrcodes"):
        os.makedirs("qrcodes")
    caminho = f"qrcodes/{str(unidade)}.png"
    if not os.path.exists(caminho):
        img = qrcode.make(str(unidade))
        img.save(caminho)
    return caminho


def gerar_pdf_etiquetas_qr(lista_unidades, nome_pdf="Etiquetas_A4.pdf"):
    c = canvas.Canvas(nome_pdf, pagesize=A4)
    width, height = A4
    x, y = 1.5*cm, height - 4*cm
    for unidade in lista_unidades:
        img = gerar_qr_imagem(unidade)
        c.drawImage(img, x, y, width=3.5*cm, height=3.5*cm)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(x + 1.75*cm, y - 0.4*cm, f"UNIDADE: {unidade}")
        x += 4.8*cm
        if x > width - 4*cm:
            x = 1.5*cm
            y -= 5*cm
        if y < 2*cm:
            c.showPage()
            y = height - 4*cm
    c.save()
    os.startfile(nome_pdf)  # Abre o PDF automaticamente
    return nome_pdf


def gerar_relatorio_leituras_pdf(dados, nome_pdf="Relatorio_Mensal.pdf"):
    c = canvas.Canvas(nome_pdf, pagesize=A4)
    width, height = A4
    y = height - 2*cm
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, y, "ÁguaFlow - Relatório de Leituras Mensal")
    y -= 1.5*cm

    # Títulos
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2*cm, y, "Unidade")
    c.drawString(5*cm, y, "Anterior")
    c.drawString(9*cm, y, "Atual")
    c.drawString(13*cm, y, "Consumo")
    y -= 0.6*cm

    c.setFont("Helvetica", 10)
    for row in dados:
        unid, ant, atu, cons, data = row[1], row[2], row[3], row[4], row[5]
        c.drawString(2*cm, y, str(unid))
        c.drawString(5*cm, y, f"{ant:.2f}")
        c.drawString(9*cm, y, f"{atu:.2f}")
        c.drawString(13*cm, y, f"{cons:.2f}")
        y -= 0.6*cm
        if y < 2*cm:
            c.showPage()
            y = height - 2*cm

    c.save()  # SALVAMENTO CORRIGIDO
    os.startfile(nome_pdf)  # ABRE O PDF AUTOMATICAMENTE
    return nome_pdf

# --- INTERFACE FLET (TELA) ---


def montar_tela_relatorios(page, voltar):
    def acao_gerar_pdf(e):
        dados = db.buscar_todas_leituras()  # Busca no seu banco
        if dados:
            gerar_relatorio_leituras_pdf(dados)
            page.snack_bar = ft.SnackBar(
                ft.Text("PDF de Leituras Gerado!"), open=True)
        else:
            page.snack_bar = ft.SnackBar(
                ft.Text("Nenhum dado encontrado no banco!"), open=True)
        page.update()

    def acao_gerar_etiquetas(e):
        # Exemplo: busca todas as unidades para gerar etiquetas
        unidades = [u[1] for u in db.buscar_todas_leituras()]
        if unidades:
            gerar_pdf_etiquetas_qr(unidades)
            page.snack_bar = ft.SnackBar(
                ft.Text("Etiquetas Geradas!"), open=True)
        else:
            page.snack_bar = ft.SnackBar(
                ft.Text("Sem unidades para etiquetas!"), open=True)
        page.update()

    return ft.Container(
        expand=True,
        bgcolor="#1A1C1E",
        padding=30,
        content=ft.Column([
            ft.Text("Painel de Relatórios", size=28,
                    color="white", weight="bold"),
            ft.Divider(color="white10"),
            ft.ElevatedButton(
                "GERAR PDF DE LEITURAS", icon=ft.Icons.PICTURE_AS_PDF, on_click=acao_gerar_pdf, width=300),
            ft.ElevatedButton("GERAR ETIQUETAS QR", icon=ft.Icons.QR_CODE,
                              on_click=acao_gerar_etiquetas, width=300),
            ft.Container(height=20),
            ft.TextButton("Voltar ao Menu", on_click=lambda _: voltar())
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )
