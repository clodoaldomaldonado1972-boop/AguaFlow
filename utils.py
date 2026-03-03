from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# --- 1. FUNÇÃO DE ETIQUETAS QR ---


def gerar_pdf_etiquetas_qr(lista_unidades):
    nome_pdf = "Etiquetas_QR_Vivere.pdf"
    c = canvas.Canvas(nome_pdf, pagesize=A4)
    width, height = A4

    colunas, linhas = 4, 6
    margem_x, margem_y = 1.5 * cm, 2 * cm
    espaco_x, espaco_y = 4.5 * cm, 4.5 * cm
    tamanho_qr = 3.5 * cm

    x_atual = margem_x
    y_atual = height - margem_y - tamanho_qr
    cont_col = 0
    cont_lin = 0

    for unidade in lista_unidades:
        caminho_img = f"qr_codes/{unidade}.png"
        if os.path.exists(caminho_img):
            c.drawImage(caminho_img, x_atual, y_atual,
                        width=tamanho_qr, height=tamanho_qr)
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(x_atual + (tamanho_qr/2),
                                y_atual - 15, unidade.replace("_", " "))

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

# --- 2. FUNÇÃO DE RELATÓRIO DE LEITURAS ---


def gerar_relatorio_leituras_pdf(dados):
    nome_arquivo = "relatorio_mensal.pdf"
    c = canvas.Canvas(nome_arquivo, pagesize=letter)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "Relatório de Leituras - Vivere Prudente")

    y = 700
    c.setFont("Helvetica", 10)
    for r in dados:
        texto = f"Unidade: {r[0]:<15} | Água: {r[1]:>6} m3 | Gás: {r[2]:>6} | Data: {r[3]}"
        c.drawString(100, y, texto)
        y -= 20
        if y < 50:
            c.showPage()
            y = 750
            c.setFont("Helvetica", 10)

    c.save()  # ESSENCIAL: Salva o arquivo antes de tentar enviar
    return nome_arquivo

# --- 3. FUNÇÃO DE ENVIO DE E-MAIL ---


def enviar_email_com_pdf(destinatario, caminho_pdf):
    # Lembre-se de usar a "Senha de App" do Google
    meu_email = "seu_email@gmail.com"
    minha_senha = "sua_senha_de_app"

    msg = MIMEMultipart()
    msg['From'] = meu_email
    msg['To'] = destinatario
    msg['Subject'] = "Relatório de Leituras - Vivere Prudente"

    msg.attach(MIMEText("Olá, segue o relatório em anexo.", 'plain'))

    try:
        with open(caminho_pdf, "rb") as anexo:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(anexo.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition', f"attachment; filename= {os.path.basename(caminho_pdf)}")
            msg.attach(part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(meu_email, minha_senha)
        server.sendmail(meu_email, destinatario, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Erro no e-mail: {e}")
        return False
