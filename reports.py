import os
import qrcode
import smtplib
import flet as ft
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
import database as db

# --- 1. FUNÇÕES DE APOIO (QR CODE E E-MAIL) ---


def gerar_qr_imagem(unidade):
    if not os.path.exists("qrcodes"):
        os.makedirs("qrcodes")
    caminho = f"qrcodes/{str(unidade)}.png"
    if not os.path.exists(caminho):
        img = qrcode.make(str(unidade))
        img.save(caminho)
    return caminho


def enviar_email_com_relatorio(caminho_arquivo):
    """Lógica de envio via SMTP."""
    meu_email = "seu_email@gmail.com"  # <--- Altere aqui
    senha_app = "xxxx xxxx xxxx xxxx"   # <--- Senha de App do Google
    destinatario = "administracao@condominio.com"

    if not os.path.exists(caminho_arquivo):
        return False

    msg = MIMEMultipart()
    msg['From'] = meu_email
    msg['To'] = destinatario
    msg['Subject'] = f"Relatório de Medição ÁguaFlow - {os.path.basename(caminho_arquivo)}"

    corpo = "Olá,\n\nSegue em anexo o relatório de medições de água atualizado.\n\nAtenciosamente,\nSistema ÁguaFlow"
    msg.attach(MIMEText(corpo, 'plain'))

    with open(caminho_arquivo, "rb") as anexo:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(anexo.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        f"attachment; filename= {os.path.basename(caminho_arquivo)}")
        msg.attach(part)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(meu_email, senha_app)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False

# --- 2. GERAÇÃO DE PDFS ---


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
    os.startfile(nome_pdf)
    return nome_pdf


def gerar_relatorio_leituras_pdf(dados, nome_pdf="Relatorio_Mensal.pdf"):
    c = canvas.Canvas(nome_pdf, pagesize=A4)
    width, height = A4

    def desenhar_cabecalho(canvas_obj, y_pos):
        canvas_obj.setFont("Helvetica-Bold", 14)
        canvas_obj.drawString(
            2*cm, y_pos, "ÁguaFlow - Relatório de Leituras Mensal")
        y_pos -= 0.8*cm
        canvas_obj.setFont("Helvetica-Bold", 10)
        canvas_obj.drawString(2*cm, y_pos, "Unidade")
        canvas_obj.drawString(5*cm, y_pos, "Anterior")
        canvas_obj.drawString(9*cm, y_pos, "Atual")
        canvas_obj.drawString(13*cm, y_pos, "Consumo")
        canvas_obj.line(2*cm, y_pos - 0.2*cm, 19*cm, y_pos - 0.2*cm)
        return y_pos - 0.8*cm

    y = height - 2*cm
    y = desenhar_cabecalho(c, y)
    soma_consumo = 0
    contagem = 0

    c.setFont("Helvetica", 10)
    for row in dados:
        unid, ant, atu, cons = row[1], row[2], row[3], row[4]
        if cons is not None:
            soma_consumo += cons
            contagem += 1

        txt_ant = f"{ant:.2f}" if ant is not None else "0.00"
        txt_atu = f"{atu:.2f}" if atu is not None else "0.00"
        txt_cons = f"{cons:.2f}" if cons is not None else "0.00"

        c.drawString(2*cm, y, str(unid))
        c.drawString(5*cm, y, txt_ant)
        c.drawString(9*cm, y, txt_atu)
        c.drawString(13*cm, y, txt_cons)
        y -= 0.6*cm

        if y < 3*cm:
            c.showPage()
            y = height - 2*cm
            y = desenhar_cabecalho(c, y)
            c.setFont("Helvetica", 10)

    media = soma_consumo / contagem if contagem > 0 else 0
    y -= 1*cm
    c.line(2*cm, y + 0.8*cm, 19*cm, y + 0.8*cm)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, y, f"Consumo Total: {soma_consumo:.2f} m³")
    c.drawString(10*cm, y, f"Média por Unidade: {media:.2f} m³")
    c.save()
    os.startfile(nome_pdf)
    return nome_pdf

# --- 3. INTERFACE FLET ---


def montar_tela_relatorios(page, voltar):
    dados_atuais = db.buscar_todas_leituras()
    total_m3 = sum(row[4] for row in dados_atuais if row[4] is not None)
    total_unid = len([row for row in dados_atuais if row[3] is not None])

    def acao_gerar_pdf(e):
        dados = db.buscar_todas_leituras()
        if dados:
            gerar_relatorio_leituras_pdf(dados)
            page.snack_bar = ft.SnackBar(
                ft.Text("PDF Gerado com Sucesso!"), open=True)
        page.update()

    def acao_enviar_email(e):
        caminho = "Relatorio_Mensal.pdf"
        sucesso = enviar_email_com_relatorio(caminho)
        if sucesso:
            page.snack_bar = ft.SnackBar(
                ft.Text("E-mail enviado com sucesso!"), open=True)
        else:
            page.snack_bar = ft.SnackBar(
                ft.Text("Erro no envio. Verifique o arquivo e as credenciais."), open=True)
        page.update()

    resumo_card = ft.Container(
        content=ft.Column([
            ft.Text("RESUMO DAS LEITURAS", size=14,
                    weight="bold", color="white70"),
            ft.Row([
                ft.Icon(ft.Icons.WATER_DROP, color="blue"),
                ft.Text(f"{total_m3:.2f} m³", size=32,
                        weight="bold", color="blue"),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Text(f"{total_unid} unidades lidas", size=12, color="white54")
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor="#25282B", padding=20, border_radius=15, width=350
    )

    return ft.Container(
        expand=True, bgcolor="#1A1C1E", padding=30,
        content=ft.Column([
            ft.Text("Painel de Relatórios", size=28,
                    color="white", weight="bold"),
            ft.Divider(color="white10"),
            resumo_card,
            ft.Container(height=20),
            ft.ElevatedButton("GERAR PDF DE LEITURAS", icon=ft.Icons.PICTURE_AS_PDF,
                              on_click=acao_gerar_pdf, width=350, height=50),
            ft.ElevatedButton("GERAR ETIQUETAS QR", icon=ft.Icons.QR_CODE, on_click=lambda _: gerar_pdf_etiquetas_qr(
                [u[1] for u in db.buscar_todas_leituras()]), width=350, height=50),
            ft.ElevatedButton("ENVIAR POR E-MAIL", icon=ft.Icons.EMAIL, on_click=acao_enviar_email,
                              width=350, height=50, bgcolor="white10", color="white70"),
            ft.Container(height=20),
            ft.TextButton("Voltar ao Menu", on_click=lambda _: voltar())
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO)
    )
