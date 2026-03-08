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
    senha_app = "xxxx xxxx xxxx xxxx"
    destinatario = "administracao@condominio.com"

    if not os.path.exists(caminho_arquivo):
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
                'Content-Disposition', f"attachment; filename= {os.path.basename(caminho_arquivo)}")
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

# --- 2. GERAÇÃO DE PDFS (CORRIGIDO) ---


def gerar_relatorio_leituras_pdf(dados, nome_pdf="Relatorio_Mensal.pdf"):
    c = canvas.Canvas(nome_pdf, pagesize=A4)
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

    y = height - 2*cm
    y = desenhar_cabecalho(c, y)
    soma_consumo = 0
    contagem = 0

    for row in dados:
        # Mapeamento: 0:unid, 1:atual, 2:anterior, 3:data_atual, 4:data_anterior
        unid = str(row[0])
        atu_val = row[1]
        ant_val = row[2]
        dt_atu = row[3] if row[3] else "--/--/--"
        dt_ant = row[4] if row[4] else "--/--/--"

        # --- CORREÇÃO DO ERRO DE FORMATAÇÃO ---
        try:
            atu = float(atu_val) if atu_val is not None else 0.0
            ant = float(ant_val) if ant_val is not None else 0.0
        except:
            atu, ant = 0.0, 0.0

        consumo = max(0, atu - ant) if atu_val is not None else 0.0
        soma_consumo += consumo
        if atu_val is not None:
            contagem += 1

        c.setFont("Helvetica", 9)
        c.drawString(1.5*cm, y, unid)

        # Formata: "0.00 (data)"
        c.drawString(4.0*cm, y, f"{ant:.2f} ({dt_ant[:10]})")
        c.drawString(9.5*cm, y, f"{atu:.2f} ({dt_atu[:10]})")

        c.setFont("Helvetica-Bold", 9)
        c.drawString(15.5*cm, y, f"{consumo:.2f} m³")

        y -= 0.5*cm
        if y < 3*cm:
            c.showPage()
            y = height - 2*cm
            y = desenhar_cabecalho(c, y)

    # Rodapé
    y -= 1*cm
    c.line(1.5*cm, y + 0.8*cm, 19.5*cm, y + 0.8*cm)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(1.5*cm, y, f"Total do Condomínio: {soma_consumo:.2f} m³")
    media = soma_consumo / contagem if contagem > 0 else 0
    c.drawString(12*cm, y, f"Média/Unid: {media:.2f} m³")

    c.save()
    if os.name == 'nt':
        os.startfile(nome_pdf)
    return nome_pdf

# --- 3. INTERFACE FLET ---


def montar_tela_relatorios(page, voltar):
    dados_atuais = db.buscar_todas_leituras()

    # Cálculo seguro do resumo
    consumo_total = 0
    lidos = 0
    for r in dados_atuais:
        if r[1] is not None:  # r[1] é leitura_atual
            lidos += 1
            try:
                consumo_total += (float(r[1]) - float(r[2]))
            except:
                pass

    def acao_gerar_pdf(e):
        dados = db.buscar_todas_leituras()
        if dados:
            gerar_relatorio_leituras_pdf(dados)
            page.snack_bar = ft.SnackBar(ft.Text("PDF Gerado!"), open=True)
            page.update()

    resumo_card = ft.Container(
        content=ft.Column([
            ft.Text("RESUMO MENSAL", size=14, weight="bold", color="white70"),
            ft.Row([
                ft.Icon(ft.Icons.WATER_DROP, color="blue"),
                ft.Text(f"{max(0, consumo_total):.2f} m³",
                        size=32, weight="bold", color="blue"),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Text(f"{lidos} de {len(dados_atuais)} unidades lidas",
                    size=12, color="white54")
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
            ft.ElevatedButton("ENVIAR POR E-MAIL", icon=ft.Icons.EMAIL,
                              on_click=lambda _: None, width=350, height=50, bgcolor="white10"),
            ft.TextButton("Voltar ao Menu", on_click=lambda _: voltar())
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )
