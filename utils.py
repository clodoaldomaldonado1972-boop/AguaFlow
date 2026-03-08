import os
import smtplib
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import gestao_periodos
import flet as ft
import gerador_pdf  # <--- IMPORTANDO O NOVO MÓDULO DE PDF

# --- 1. FUNÇÃO DE E-MAIL ---


def enviar_email_com_pdf(destinatario, caminho_pdf):
    meu_email = "clodoaldomaldonado112@gmail.com"
    minha_senha = "uhviwhsjjxmcbboh"

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

# --- 2. INTERFACE DE AJUDA ---


def montar_tela_ajuda(page, voltar):
    def acao_reset(e):
        def confirmar_reset(e):
            email_responsavel = "clodoaldomaldonado112@gmail.com"
            # O gestao_periodos deve chamar gerador_pdf.gerar_relatorio_consumo internamente
            sucesso = gestao_periodos.finalizar_mes_e_enviar(email_responsavel)

            if sucesso:
                dlg.open = False
                page.snack_bar = ft.SnackBar(ft.Text(
                    "Sucesso! Relatório enviado e novo mês iniciado."), bgcolor="green", open=True)
                page.update()
                voltar()
            else:
                page.snack_bar = ft.SnackBar(ft.Text(
                    "ERRO: Verifique sua senha de e-mail ou internet."), bgcolor="red", open=True)
                page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Confirmar Reset Mensal?"),
            content=ft.Text(
                "O sistema enviará o PDF ao escritório e preparará o novo mês."),
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
Agora com datas de leitura atual e anterior impressas.
### 3. Virada de Mês
O envio agora é automático ao clicar no botão abaixo.
            """),
            ft.Container(height=20),
            ft.ElevatedButton(
                "ENVIAR RELATÓRIO E INICIAR NOVO MÊS",
                icon=ft.Icons.SEND_AND_ARCHIVE,
                bgcolor="red",
                color="white",
                on_click=acao_reset,
                width=400
            ),
            ft.TextButton("Voltar ao Menu", on_click=lambda _: voltar())
        ], scroll=ft.ScrollMode.AUTO)
    )
