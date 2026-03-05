import os
import smtplib
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

# --- 1. FUNÇÃO DE ETIQUETAS QR ---
def gerar_pdf_etiquetas_qr(lista_unidades):
    nome_pdf = "Etiquetas_QR_Vivere.pdf"
    # Criar pasta se não existir
    if not os.path.exists("qr_codes"):
        os.makedirs("qr_codes")

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
        # unidade: (id, numero, bloco)
        numero_apto = str(unidade[1])
        bloco = str(unidade[2])
        caminho_img = f"qr_codes/{numero_apto}.png"

        if os.path.exists(caminho_img):
            c.drawImage(caminho_img, x_atual, y_atual, width=tamanho_qr, height=tamanho_qr)
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(x_atual + (tamanho_qr/2), y_atual - 15, f"Unid: {numero_apto}-{bloco}")

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

    def desenhar_cabecalho(canvas_obj, y_pos):
        canvas_obj.setFont("Helvetica-Bold", 16)
        canvas_obj.drawString(100, y_pos, "Relatório de Leituras - Vivere Prudente")
        canvas_obj.setFont("Helvetica-Bold", 10)
        canvas_obj.drawString(100, y_pos - 30, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        return y_pos - 60

    y = desenhar_cabecalho(c, 750)
    c.setFont("Courier", 10) 

    for r in dados:
        # r: (id, numero, bloco, valor, status)
        txt_unid = f"{r[1]}-{r[2]}" 
        txt_valor = f"{r[3] if r[3] else '---'}"
        txt_status = f"{r[4]}"

        linha = f"Unid: {txt_unid:<10} | Valor: {txt_valor:>8} | Status: {txt_status}"
        c.drawString(100, y, linha)
        y -= 20

        if y < 50:
            c.showPage()
            y = desenhar_cabecalho(c, 750)
            c.setFont("Courier", 10)

    c.save()
    return nome_arquivo

# --- 3. FUNÇÃO DE ENVIO DE E-MAIL ---
def enviar_email_com_pdf(destinatario, caminho_pdf):
    meu_email = "clodoaldomaldonado112@gmail.com"
    # Lembre-se: Use a sua senha de 16 dígitos atualizada
    minha_senha = "jbtxbeqxfslfufgn" 
    
    data_atual = datetime.now().strftime('%d/%m/%Y')
    
    msg = MIMEMultipart()
    # Ajuste: Nome do remetente amigável
    msg['From'] = f"Sistema AguaFlow <{meu_email}>"
    msg['To'] = destinatario
    # Ajuste: Assunto com data automática
    msg['Subject'] = f"💧 Relatório AguaFlow - Vivere Prudente - {data_atual}"

    # Ajuste: Corpo do e-mail mais profissional
    corpo = f"""
    Olá,
    
    Segue em anexo o relatório de leituras de água do condomínio Vivere Prudente.
    
    📅 Data de referência: {data_atual}
    📄 Arquivo: {os.path.basename(caminho_pdf)}
    
    Este é um envio automático do sistema AguaFlow. Por favor, não responda a este e-mail.
    
    Atenciosamente,
    Equipe Técnica AguaFlow.
    """
    msg.attach(MIMEText(corpo, 'plain'))

    try:
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
        server.sendmail(meu_email, destinatario, msg.as_string())
        server.quit()
        print("✅ E-mail enviado com sucesso!")
        return True
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")
        return False
    