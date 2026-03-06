import os
import qrcode
import smtplib
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas

import flet as ft

def montar_tela_ajuda(ao_voltar):
    """Retorna o componente visual do Guia do Usuário"""
    return ft.Container(
        # --- AS TRAVAS ANTI-BRANCO ---
        expand=True,           # Força o container a ocupar a tela toda
        bgcolor="#1A1C1E",     # Define a cor escura explicitamente
        padding=20,
        # ----------------------------
        content=ft.Column([
            ft.Text("❓ Guia de Operação", size=20, weight="bold", color="blue"),
            ft.Divider(color="white10"),
            ft.Text("1. Iniciar Leitura: Escaneie o QR da unidade e digite o valor.", size=16, color="white"),
            ft.Text("2. Etiquetas: Admin gera PDF para impressão A4.", size=16, color="white"),
            ft.Text("3. Fechar Mês: Move dados para histórico (SÓ ADMIN).", size=16, color="white"),
            ft.Container(height=20), # Espaçamento
            ft.ElevatedButton(
                "VOLTAR AO MENU", 
                icon=ft.Icons.ARROW_BACK, 
                on_click=ao_voltar,
                style=ft.ButtonStyle(color="white")
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )

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
        caminho_img = f"qrcodes/{unidade}.png" 
        if os.path.exists(caminho_img):
            c.drawImage(caminho_img, x_atual, y_atual, width=tamanho_qr, height=tamanho_qr)
        
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

    def desenhar_cabecalho(canvas_obj, y_pos):
        canvas_obj.setFont("Helvetica-Bold", 16)
        canvas_obj.drawString(
            100, y_pos, "Relatório de Leituras - Vivere Prudente")
        canvas_obj.setFont("Helvetica-Bold", 10)
        canvas_obj.drawString(
            100, y_pos - 30, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        return y_pos - 60

    y = desenhar_cabecalho(c, 750)
    c.setFont("Helvetica", 10)

    for r in dados:
        # r[0]=unidade, r[1]=agua, r[2]=gas, r[3]=data
        texto = f"Unid: {str(r[0]):<15} | Água: {str(r[1]):>6} m3 | Gás: {str(r[2]):>6} | Data: {str(r[3])}"
        c.drawString(100, y, texto)
        y -= 20

        if y < 50:
            c.showPage()
            y = desenhar_cabecalho(c, 750)
            c.setFont("Helvetica", 10)

    c.save()
    return nome_arquivo

# --- 3. FUNÇÃO DE ENVIO DE E-MAIL ---


def enviar_email_com_pdf(destinatario, caminho_pdf):
    meu_email = "clodoaldomaldonado112@gmail.com"
    # COLE AQUI AS 16 LETRAS QUE O GOOGLE GEROU
    minha_senha = "cuxiizdglmgilxgw"
    msg = MIMEMultipart()
    msg['From'] = meu_email
    msg['To'] = destinatario
    msg['Subject'] = "Relatório de Leituras - Vivere Prudente"
    msg.attach(MIMEText("Olá, segue o relatório em anexo.", 'plain'))

    try:
        if not os.path.exists(caminho_pdf):
            print(f"Erro: O arquivo {caminho_pdf} não foi encontrado.")
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
        server.sendmail(meu_email, destinatario, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Erro no e-mail: {e}")
        return False

def gerar_qr_unidade(unidade):
    import qrcode
    import os
    
    # 1. Cria a pasta se ela não existir
    if not os.path.exists("qrcodes"):
        os.makedirs("qrcodes")
    
    # 2. Limpa o nome da unidade para evitar erro de arquivo (remove / ou \)
    nome_arquivo = str(unidade).replace("/", "-").replace("\\", "-")
    caminho = f"qrcodes/{nome_arquivo}.png"
    
    # 3. Gera o QR Code
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(str(unidade))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 4. Salva a imagem
    img.save(caminho)
    return caminho