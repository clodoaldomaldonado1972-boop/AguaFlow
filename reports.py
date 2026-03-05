import os
import smtplib
import qrcode
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

# --- 1. FUNÇÃO DE QR CODES ---
def gerar_qr_unidade(unidade):
    if not os.path.exists("qrcodes"):
        os.makedirs("qrcodes")
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(unidade)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    caminho = f"qrcodes/{unidade}.png"
    img.save(caminho)
    return caminho

# --- 2. FUNÇÃO DE ETIQUETAS PDF ---
ddef gerar_pdf_etiquetas_qr(lista_unidades):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    import os

    nome_pdf = "Etiquetas_QR_Vivere.pdf"
    c = canvas.Canvas(nome_pdf, pagesize=A4)
    width, height = A4

    # Configuração da Grade
    colunas, linhas = 4, 6
    margem_x, margem_y = 1.5 * cm, 2 * cm
    espaco_x, espaco_y = 4.5 * cm, 4.5 * cm
    tamanho_qr = 3.5 * cm

    x_atual, y_atual = margem_x, height - margem_y - tamanho_qr
    cont_col, cont_lin = 0, 0

    for unidade in lista_unidades:
        # Importante: Garantir que o nome do arquivo bate com o gerado pela função de QR
        caminho_img = f"qrcodes/{str(unidade).replace('/', '-')}.png" 
        
        if os.path.exists(caminho_img):
            c.drawImage(caminho_img, x_atual, y_atual, width=tamanho_qr, height=tamanho_qr)
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(x_atual + (tamanho_qr/2), y_atual - 15, str(unidade))

            # Lógica de movimentação na página
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
        else:
            print(f"Aviso: Imagem não encontrada para {unidade}")

    c.save()
    return nome_pdf

# --- 3. RELATÓRIO DE LEITURAS (Corrigido para o novo Banco) ---
def gerar_relatorio_leituras_pdf(dados):
    nome_arquivo = f"Relatorio_AguaFlow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    c = canvas.Canvas(nome_arquivo, pagesize=letter)

    def desenhar_cabecalho(canvas_obj, y_pos):
        canvas_obj.setFont("Helvetica-Bold", 16)
        canvas_obj.drawString(100, y_pos, "Relatório de Leituras - Vivere Prudente")
        canvas_obj.setFont("Helvetica-Bold", 10)
        canvas_obj.drawString(100, y_pos - 30, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        return y_pos - 60

    y = desenhar_cabecalho(c, 750)
    c.setFont("Courier", 10) # Courier mantém o alinhamento das colunas fixo

    for r in dados:
        # r[1] = Unidade, r[3] = Leitura Atual
        unid = str(r[1])
        # Garante que se o valor for None (não lido), apareça "---"
        leitura = f"{r[3]:.2f}" if r[3] is not None else "PENDENTE"
        
        texto = f"Unid: {unid:<10} | Leitura Atual: {leitura:>10} m3"
        c.drawString(100, y, texto)
        y -= 20

        if y < 50:
            c.showPage()
            y = desenhar_cabecalho(c, 750)
            c.setFont("Courier", 10)

    c.save()
    return nome_arquivo

# --- 4. ENVIO DE E-MAIL ---
def enviar_email_com_pdf(destinatario, caminho_pdf):
    # Lembre-se: Use "Senhas de App" do Google se tiver 2 fatores ativado
    meu_email = "clodoaldomaldonado112@gmail.com"
    minha_senha = "cuxiizdglmgilxgw"  # <--- COLE AQUI AS 16 LETRAS QUE O GOOGLE GEROU

    msg = MIMEMultipart()
    msg['From'], msg['To'], msg['Subject'] = meu_email, destinatario, "Relatório ÁguaFlow - Vivere Prudente"
    msg.attach(MIMEText(f"Olá,\n\nSegue em anexo o relatório de consumo gerado em {datetime.now().strftime('%d/%m/%Y')}.\n\nAtenciosamente,\nEquipe ÁguaFlow.", 'plain'))

    try:
        if os.path.exists(caminho_pdf):
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
            return True
        return False
    except Exception as e:
        print(f"Erro no e-mail: {e}")
        return False