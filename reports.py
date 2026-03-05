import os
import qrcode
import smtplib
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

# --- 1. FUNÇÃO DE ETIQUETAS QR ---
def gerar_pdf_etiquetas_qr(lista_unidades):
    nome_pdf = "Etiquetas_QR_Vivere.pdf"
    
    if not os.path.exists("qr_codes"):
        os.makedirs("qr_codes")

    for unidade in lista_unidades:
        numero_apto = str(unidade[1])
        caminho_img = f"qr_codes/{numero_apto}.png"
        if not os.path.exists(caminho_img):
            qr = qrcode.QRCode(version=1, box_size=10, border=2)
            qr.add_data(numero_apto)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(caminho_img)

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
    print(f"✅ PDF de etiquetas gerado com sucesso: {nome_pdf}")
    return nome_pdf

# --- 2. FUNÇÃO DE RELATÓRIO DE LEITURAS ---
def gerar_relatorio_leituras_pdf(dados):
    nome_arquivo = "relatorio_mensal.pdf"
    c = canvas.Canvas(nome_arquivo, pagesize=A4)
    largura, altura = A4

    def desenhar_cabecalho(canvas_obj, y_pos):
        canvas_obj.setFont("Helvetica-Bold", 16)
        canvas_obj.drawString(50, y_pos, "Relatório de Consumo de Água - Vivere Prudente")
        canvas_obj.setFont("Helvetica", 10)
        data_str = datetime.now().strftime('%d/%m/%Y %H:%M')
        canvas_obj.drawString(50, y_pos - 20, f"Gerado em: {data_str}")
        
        y_tab = y_pos - 50
        canvas_obj.setFont("Helvetica-Bold", 10)
        canvas_obj.drawString(50, y_tab, "UNIDADE")
        canvas_obj.drawString(130, y_tab, "ANT. (m³)")
        canvas_obj.drawString(210, y_tab, "ATUAL (m³)")
        canvas_obj.drawString(290, y_tab, "CONS. (m³)")
        canvas_obj.drawString(370, y_tab, "MÉDIA")
        canvas_obj.drawString(450, y_tab, "STATUS")
        canvas_obj.line(50, y_tab - 5, 550, y_tab - 5)
        return y_tab - 20

    y = desenhar_cabecalho(c, altura - 50)
    c.setFont("Courier", 10)

    for r in dados:
        unid = f"{r[1]}-{r[2]}"
        atual = float(r[3]) if r[3] else 0.0
        anterior = float(r[4]) if r[4] else 0.0
        consumo = atual - anterior
        status = str(r[5])

        # AQUI ESTAVA O ERRO (Linhas 105-110 corrigidas em linha única)
        c.drawString(50, y, f"{unid:<10}")
        c.drawString(130, y, f"{anterior:>8.2f}")
        c.drawString(210, y, f"{atual:>8.2f}")
        c.drawString(290, y, f"{consumo:>8.2f}")
        c.drawString(370, y, f"{'---':>8}")
        c.drawString(450, y, f"{status}")

        y -= 15
        if y < 50:
            c.showPage()
            y = desenhar_cabecalho(c, altura - 50)
            c.setFont("Courier", 10)

    c.save()
    return nome_arquivo

# --- 3. FUNÇÃO DE ENVIO DE E-MAIL ---
def enviar_email_com_pdf(destinatario, caminho_pdf):
    meu_email = "clodoaldomaldonado112@gmail.com"
    minha_senha = "jbtxbeqxfslfufgn" 
    
    msg = MIMEMultipart()
    msg['From'] = f"Sistema AguaFlow <{meu_email}>"
    msg['To'] = destinatario
    msg['Subject'] = f"💧 Relatório AguaFlow - {datetime.now().strftime('%d/%m/%Y')}"

    corpo = "Segue em anexo o relatório detalhado de consumo de água (Vivere Prudente)."
    msg.attach(MIMEText(corpo, 'plain'))

    try:
        with open(caminho_pdf, "rb") as anexo:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(anexo.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f"attachment; filename={os.path.basename(caminho_pdf)}")
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
    