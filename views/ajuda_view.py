import flet as ft
import asyncio
import urllib.parse
import views.styles as st
from utils.logger_config import enviar_report_erro


def montar_tela_ajuda(page: ft.Page, on_back):
    # Captura dados dinâmicos para a mensagem
    user_data = getattr(page, "user_data", {}) or {}
    nome_leiturista = user_data.get('nome', 'Não identificado')

    # Lógica da Mensagem para suporte
    corpo_mensagem = (
        "Olá! Suporte AguaFlow. Estou no Condomínio Vivere Prudente e preciso de auxílio técnico.\n"
        f"Leiturista: {nome_leiturista}\n"
        "Aparelho: Android - AguaFlow v1.2.0\n"
        f"Contexto: {page.route}"
    )

    # Geração da URL segura via wa.me
    url_suporte = f"https://wa.me/5518981337316?text={urllib.parse.quote(corpo_mensagem)}"

    async def disparar_teste_erro(e):
        """Simula um erro de conexão e dispara o e-mail de alerta em background."""
        e.control.disabled = True
        e.control.text = "ENVIANDO TESTE..."
        page.update()

        try:
            # Força um erro de conexão simulado para o relatório
            erro_simulado = "SimulatedConnectionError: [TESTE] Falha ao alcançar o servidor Supabase (Timeout 30s)."

            # Executa o envio em uma thread separada para não travar a interface Flet
            # enviar_report_erro utiliza smtplib que é uma biblioteca bloqueante
            await asyncio.to_thread(
                enviar_report_erro,
                mensagem_erro=erro_simulado,
                unidade="DEBUG-HALL",
                leiturista=nome_leiturista
            )
            page.show_dialog(ft.SnackBar(ft.Text(
                "✅ E-mail de teste enviado! Verifique o destinatário."), bgcolor=st.SUCCESS_GREEN))
        except Exception as ex:
            page.show_dialog(ft.SnackBar(
                ft.Text(f"❌ Erro no envio do teste: {ex}"), bgcolor="red"))

        e.control.disabled = False
        e.control.text = "TESTE DE RELATÓRIO"
        page.update()

    return ft.View(
        route="/ajuda",
        bgcolor=st.BG_DARK,
        appbar=ft.AppBar(
            title=ft.Text("Ajuda e Suporte"),
            bgcolor=st.PRIMARY_BLUE,
            leading=ft.IconButton("arrow_back", on_click=on_back),
        ),
        controls=[
            ft.Column(
                [
                    ft.Container(height=20),
                    ft.Icon("help_center_outlined", size=80, color=st.PRIMARY_BLUE),
                    ft.Text("Suporte Técnico", size=24, weight="bold", color="white"),
                    ft.Container(height=20),
                    ft.ElevatedButton(
                        "CHAMAR SUPORTE NO WHATSAPP",
                        icon="whatsapp",
                        style=st.BTN_SPECIAL,
                        on_click=lambda _: page.launch_url(url_suporte),
                        width=320, height=60
                    ),
                    ft.ElevatedButton(
                        "TESTE DE RELATÓRIO",
                        icon="email_outlined",
                        on_click=disparar_teste_erro,
                        width=320, height=60
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
            )
        ]
    )
