import os
import qrcode
import smtplib
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from io import BytesIO
import base64

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
import flet as ft
import database as db

# --- 1. FUNÇÕES DE E-MAIL ---


def enviar_email_com_pdf(destinatario, caminho_pdf):
    meu_email = "clodoaldomaldonado112@gmail.com"
    minha_senha = "gbywnwkhoozolenj"  # Senha de App de 16 dígitos

    msg = MIMEMultipart()
    msg['From'] = meu_email
    msg['To'] = destinatario
    msg['Subject'] = "Relatório de Leituras - Vivere Prudente"
    msg.attach(MIMEText("Olá, segue o relatório em anexo.", 'plain'))

    try:
        if not os.path.exists(caminho_pdf):
            return False

        with open(caminho_pdf, "rb") as anexo:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(anexo.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition', f"attachment; filename={os.path.basename(caminho_pdf)}")
            msg.attach(part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(meu_email, minha_senha)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Erro no e-mail: {e}")
        return False

# --- 2. GERAÇÃO DE PDFS (ETIQUETAS E RELATÓRIO) ---


def gerar_pdf_etiquetas_qr(lista_unidades):
    nome_pdf = "Etiquetas_QR_Vivere.pdf"
    c = canvas.Canvas(nome_pdf, pagesize=A4)
    width, height = A4
    colunas, linhas = 4, 6
    margem_x, margem_y = 1.5 * cm, 2 * cm
    espaco_x, espaco_y = 4.5 * cm, 4.5 * cm
    tamanho_qr = 3.5 * cm

    x_atual, y_atual = margem_x, height - margem_y - tamanho_qr
    cont_col = cont_lin = 0

    for unidade in lista_unidades:
        caminho_img = f"qrcodes/{unidade}.png"
        if os.path.exists(caminho_img):
            c.drawImage(caminho_img, x_atual, y_atual,
                        width=tamanho_qr, height=tamanho_qr)
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(x_atual + (tamanho_qr/2),
                                y_atual - 15, str(unidade).replace("_", " "))

            cont_col += 1
            x_atual += espaco_x
            if cont_col >= colunas:
                cont_col, x_atual = 0, margem_x
                y_atual -= espaco_y
                cont_lin += 1
            if cont_lin >= linhas:
                c.showPage()
                y_atual = height - margem_y - tamanho_qr
                cont_lin = 0
    c.save()
    return nome_pdf


def gerar_relatorio_leituras_pdf(dados):
    nome_arquivo = "relatorio_mensal.pdf"
    c = canvas.Canvas(nome_arquivo, pagesize=letter)

    def cabecalho(canvas_obj, y_p):
        canvas_obj.setFont("Helvetica-Bold", 16)
        canvas_obj.drawString(
            100, y_p, "Relatório de Leituras - Vivere Prudente")
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.drawString(
            100, y_p - 20, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        return y_p - 60

    y = cabecalho(c, 750)
    for r in dados:
        texto = f"Unid: {str(r[0]):<10} | Água: {str(r[1]):>6} m3 | Gás: {str(r[2]):>6} | Data: {str(r[3])}"
        c.drawString(100, y, texto)
        y -= 20
        if y < 50:
            c.showPage()
            y = cabecalho(c, 750)
    c.save()
    return nome_arquivo

# --- 3. INTERFACE DE AJUDA E RESET ---


def montar_tela_ajuda(page, voltar):
    def acao_reset(e):
        def confirmar_reset(e):
            # 1. Força o reset no banco
    db.resetar_mes_novo()

    # 2. Fecha o alerta
    dlg.open = False
    page.update()

    # --- 3. INTERFACE DE AJUDA E RESET ---


d  # --- 3. INTERFACE DE AJUDA E RESET ---


def montar_tela_ajuda(page, voltar):
    def acao_reset(e):
        def confirmar_reset(e):
            # AQUI ESTÁ O SEGREDO: Tudo o que a função faz precisa de recuo (Tab)
            db.resetar_mes_novo()
            dlg.open = False
            page.update()
            voltar()  # Volta ao menu e limpa o erro de 'None'

        # O Alerta também precisa estar dentro da função 'acao_reset'
        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar Reset Mensal?"),
            content=ft.Text(
                "Isso zerará as leituras atuais para começar o novo mês."),
            actions=[
                ft.TextButton("Confirmar", on_click=confirmar_reset,
                              style=ft.ButtonStyle(color="red")),
                ft.TextButton("Cancelar", on_click=lambda _: (
                    setattr(dlg, "open", False), page.update()))
            ]
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    return ft.Container(
        expand=True, bgcolor="#1A1C1E", padding=30,
        content=ft.Column([
            ft.Text("MANUAL E CONFIGURAÇÕES", size=28,
                    color="white", weight="bold"),
            ft.Divider(color="white10"),
            ft.Markdown("""
### 1. Medição
O sistema segue a ordem do 16º ao 1º andar.
### 2. Relatórios
Gere o relatório antes de resetar os dados.
### 3. Virada de Mês
O botão abaixo prepara o sistema para o próximo mês.
            """),
            ft.Container(height=20),
            ft.ElevatedButton(
                "INICIAR NOVO MÊS (RESET)",
                icon=ft.Icons.RESTART_ALT,
                bgcolor="red",
                color="white",
                on_click=acao_reset,
                width=350
            ),
            ft.TextButton("Voltar ao Menu", on_click=lambda _: voltar())
        ], scroll=ft.ScrollMode.AUTO)
    )
