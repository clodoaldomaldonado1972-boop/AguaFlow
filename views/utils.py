import os
import smtplib
from datetime import datetime
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import gestao_periodos
import flet as ft

# --- 1. FUNÇÃO DE E-MAIL (Lógica Interna) ---


def enviar_email_com_pdf(destinatario, caminho_pdf):
    meu_email = "clodoaldomaldonado112@gmail.com"
    minha_senha = "uhviwhsjjxmcbboh"  # Senha de App do Google

    msg = MIMEMultipart()
    msg['From'] = meu_email
    msg['To'] = destinatario
    msg['Subject'] = "Relatório de Leituras - Vivere Prudente"
    msg.attach(MIMEText("Olá, segue o relatório em anexo.", 'plain'))

    try:
        if not os.path.exists(caminho_pdf):
            print("Erro: PDF não encontrado no caminho especificado.")
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

    def confirmar_reset(e):
        dlg.open = False
        page.update()

        page.snack_bar = ft.SnackBar(
            ft.Text("Gerando relatório e enviando e-mail..."), open=True)
        page.update()

        email_responsavel = "clodoaldomaldonado112@gmail.com"

        # Chama a lógica de fechamento de mês
        sucesso = gestao_periodos.finalizar_mes_e_enviar(email_responsavel)

        if sucesso:
            page.snack_bar = ft.SnackBar(
                ft.Text("Sucesso! Relatório enviado e banco resetado."),
                bgcolor="green", open=True)
            page.update()
            voltar()
        else:
            page.snack_bar = ft.SnackBar(
                ft.Text("ERRO ao processar. Verifique internet ou permissões."),
                bgcolor="red", open=True)
            page.update()

    # Diálogo de Confirmação
    dlg = ft.AlertDialog(
        title=ft.Text("Confirmar Reset Mensal?"),
        content=ft.Text("Isso enviará o e-mail e limpará as medições atuais."),
        actions=[
            ft.TextButton("Confirmar", on_click=confirmar_reset,
                          style=ft.ButtonStyle(color="red")),
            ft.TextButton("Cancelar", on_click=lambda _: (
                setattr(dlg, "open", False), page.update()))
        ]
    )

    def abrir_alerta(e):
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # Retorno do Container principal da interface
    return ft.Container(
        expand=True,
        bgcolor="#1A1C1E",
        padding=30,
        content=ft.Column(
            controls=[
                ft.Text("MANUAL E CONFIGURAÇÕES", size=28,
                        color="white", weight="bold"),
                ft.Divider(color="white10"),
                ft.Markdown("""
### 1. Medição
O sistema segue a ordem do 16º ao 1º andar.
### 2. Relatórios
PDFs gerados com histórico de consumo.
### 3. Virada de Mês
O envio agora é automático ao clicar no botão abaixo.
                """),
                ft.Container(height=20),

                # Botão de Ação Crítica
                ft.FilledButton(
                    content=ft.Text("ENVIAR RELATÓRIO E INICIAR NOVO MÊS"),
                    icon=ft.icons.SEND_AND_ARCHIVE,
                    style=ft.ButtonStyle(bgcolor="red", color="white"),
                    on_click=abrir_alerta,
                    width=400
                ),

                ft.TextButton(
                    "Voltar ao Menu",
                    on_click=lambda _: voltar(),
                    style=ft.ButtonStyle(color="blue")
                )
            ],
            scroll=ft.ScrollMode.AUTO,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )
