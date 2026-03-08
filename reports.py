import os
import qrcode
import smtplib
from datetime import datetime
import flet as ft
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
import database as db

# --- 1. FUNÇÕES DE APOIO ---


def gerar_qr_imagem(unidade):
    if not os.path.exists("qrcodes"):
        os.makedirs("qrcodes")
    caminho = f"qrcodes/{str(unidade)}.png"
    if not os.path.exists(caminho):
        img = qrcode.make(str(unidade))
        img.save(caminho)
    return caminho


def enviar_email_com_relatorio(caminho_arquivo):
    meu_email = "seu_email@gmail.com"
    senha_app = "xxxx xxxx xxxx xxxx"  # Lembre-se da senha de 16 dígitos do Google
    destinatario = "administracao@condominio.com"

    if not caminho_arquivo or not os.path.exists(caminho_arquivo):
        return False

    msg = MIMEMultipart()
    msg['From'] = meu_email
    msg['To'] = destinatario
    msg['Subject'] = f"Relatório ÁguaFlow - {os.path.basename(caminho_arquivo)}"

    corpo = "Olá,\n\nSegue em anexo o relatório de medições.\n\nAtenciosamente,\nSistema ÁguaFlow"
    msg.attach(MIMEText(corpo, 'plain'))

    try:
        with open(caminho_arquivo, "rb") as anexo:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(anexo.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition', f"attachment; filename={os.path.basename(caminho_arquivo)}")
            msg.attach(part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(meu_email, senha_app)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Erro e-mail: {e}")
        return False

# --- 2. GERAÇÃO DE PDFS ---


def gerar_pdf_etiquetas(lista_unidades):
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
        img_path = gerar_qr_imagem(unidade)
        c.drawImage(img_path, x + 1.2*cm, y,
                    width=tamanho_qr, height=tamanho_qr)

        centro_x = x + 1.2*cm + (tamanho_qr/2)
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(centro_x, y - 15, "VIVERE PRUDENTE")
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
    nome_pasta = datetime.now().strftime("Relatorios_%Y_%m")
    if not os.path.exists(nome_pasta):
        os.makedirs(nome_pasta)

    timestamp = datetime.now().strftime("%d_%H%M%S")
    caminho_pdf = os.path.join(nome_pasta, f"Relatorio_{timestamp}.pdf")

    c = canvas.Canvas(caminho_pdf, pagesize=A4)
    width, height = A4

    def desenhar_cabecalho(canvas_obj, y_pos):
        canvas_obj.setFont("Helvetica-Bold", 14)
        canvas_obj.drawString(
            1.5*cm, y_pos, "Vivere Flow - Relatório de Leituras")
        y_pos -= 0.8*cm
        canvas_obj.setFont("Helvetica-Bold", 9)
        canvas_obj.drawString(1.5*cm, y_pos, "Unidade")
        canvas_obj.drawString(4.0*cm, y_pos, "Anterior (Data)")
        canvas_obj.drawString(9.5*cm, y_pos, "Atual (Data)")
        canvas_obj.drawString(15.5*cm, y_pos, "Consumo")
        canvas_obj.line(1.5*cm, y_pos - 0.2*cm, 19.5*cm, y_pos - 0.2*cm)
        return y_pos - 0.6*cm

    y = desenhar_cabecalho(c, height - 2*cm)
    soma_consumo = 0
    contagem = 0

    for row in dados:
        unid = str(row[0])
        atu_val, ant_val = row[1], row[2]
        dt_atu = row[3] if row[3] else "--/--/--"
        dt_ant = row[4] if row[4] else "--/--/--"

        try:
            atu = float(atu_val) if atu_val is not None else 0.0
            ant = float(ant_val) if ant_val is not None else 0.0
        except:
            atu, ant = 0.0, 0.0

        consumo = max(0, atu - ant)
        soma_consumo += consumo
        if atu_val is not None:
            contagem += 1

        c.setFont("Helvetica", 9)
        c.drawString(1.5*cm, y, unid)
        c.drawString(4.0*cm, y, f"{ant:8.2f} ({dt_ant[:10]})")
        c.drawString(9.5*cm, y, f"{atu:8.2f} ({dt_atu[:10]})")
        c.setFont("Helvetica-Bold", 9)
        c.drawString(15.5*cm, y, f"{consumo:8.2f} m³")

        y -= 0.5*cm
        if y < 3*cm:
            c.showPage()
            y = desenhar_cabecalho(c, height - 2*cm)

    # Rodapé
    y -= 1*cm
    c.line(1.5*cm, y + 0.8*cm, 19.5*cm, y + 0.8*cm)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(1.5*cm, y, f"Total: {soma_consumo:.2f} m³")
    media = soma_consumo / contagem if contagem > 0 else 0
    c.drawString(12*cm, y, f"Média/Unid: {media:.2f} m³")

    c.save()
    if os.name == 'nt':
        os.startfile(caminho_pdf)
    return caminho_pdf

# --- 3. INTERFACE FLET ---


def montar_tela_relatorios(page, voltar):
    # Dicionário para rastrear o último arquivo gerado para o e-mail
    estado = {"ultimo_pdf": None}

    def acao_gerar_pdf(e):
        dados = db.buscar_todas_leituras()
        if dados:
            caminho = gerar_relatorio_consumo(dados)
            estado["ultimo_pdf"] = caminho
            page.snack_bar = ft.SnackBar(
                ft.Text(f"Relatório gerado em: {os.path.basename(caminho)}"), open=True)
            page.update()

    def acao_gerar_qrcodes(e):
        unidades = [str(u[0]) for u in db.buscar_todas_leituras()]
        if unidades:
            gerar_pdf_etiquetas(unidades)
            page.snack_bar = ft.SnackBar(
                ft.Text("Etiquetas QR geradas!"), open=True)
            page.update()

    def acao_enviar_email(e):
        if estado["ultimo_pdf"]:
            sucesso = enviar_email_com_relatorio(estado["ultimo_pdf"])
            texto = "E-mail enviado com sucesso!" if sucesso else "Erro ao enviar e-mail."
            page.snack_bar = ft.SnackBar(ft.Text(texto), open=True)
        else:
            page.snack_bar = ft.SnackBar(
                ft.Text("Gere o relatório primeiro!"), open=True)
        page.update()

    return ft.Container(
        expand=True, bgcolor="#1A1C1E", padding=30,
        content=ft.Column([
            ft.Text("Painel de Relatórios", size=28,
                    color="white", weight="bold"),
            ft.Divider(color="white10"),
            ft.Container(height=20),
            ft.ElevatedButton("GERAR PDF DE LEITURAS", icon=ft.Icons.PICTURE_AS_PDF,
                              on_click=acao_gerar_pdf, width=350, height=50),
            ft.ElevatedButton("GERAR ETIQUETAS QR", icon=ft.Icons.QR_CODE,
                              on_click=acao_gerar_qrcodes, width=350, height=50, bgcolor="blue800", color="white"),
            ft.ElevatedButton("ENVIAR ÚLTIMO PDF POR E-MAIL", icon=ft.Icons.EMAIL,
                              on_click=acao_enviar_email, width=350, height=50, bgcolor="white10"),
            ft.Container(height=20),
            ft.TextButton("Voltar ao Menu", on_click=lambda _: voltar())
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )
