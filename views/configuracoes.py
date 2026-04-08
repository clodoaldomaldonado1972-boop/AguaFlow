import flet as ft
import asyncio
import os
import shutil

# --- NOVOS IMPORTS CORRIGIDOS ---
# Agora buscamos da pasta utils na raiz do projeto
from utils.preferencias_leitura import PreferenciasLeitura
from utils.diagnostico import DiagnosticoSistema


def montar_tela_configs(page: ft.Page, voltar):
    # 1. Recuperação de Dados da Sessão
    user_email_logado = getattr(page, "user_email", "Visitante")

    # --- FUNÇÕES DE APOIO ---

    async def realizar_teste_sistema(e):
        btn_teste.disabled = True
        status_icon.color = "orange"
        status_text.value = "Verificando componentes..."
        page.update()

        # Chama a lógica centralizada na pasta utils
        sucesso, mensagem = await DiagnosticoSistema.executar_checkup_completo()

        status_icon.color = "green" if sucesso else "red"
        status_text.value = mensagem
        status_text.color = "green" if sucesso else "red"
        btn_teste.disabled = False
        page.update()

    def salvar_email_notificacao(e):
        email = txt_email_notif.value
        if "@" in email and "." in email:
            page.snack_bar = ft.SnackBar(
                ft.Text(f"E-mail {email} salvo para notificações!"),
                bgcolor="green"
            )
            page.snack_bar.open = True
        else:
            page.snack_bar = ft.SnackBar(
                ft.Text("E-mail inválido!"),
                bgcolor="red"
            )
            page.snack_bar.open = True
        page.update()

    def acao_sair(e):
        page.user_email = None
        page.go("/login")

    # --- COMPONENTES DE INTERFACE ---

    txt_email_notif = ft.TextField(
        label="E-mail para Alertas",
        value=user_email_logado,
        hint_text="exemplo@email.com",
        prefix_icon=ft.Icons.EMAIL_OUTLINED,
        border_color="blue",
        expand=True
    )

    status_icon = ft.Icon(ft.Icons.DASHBOARD_RENAME_KEYBOARD, color="grey")
    status_text = ft.Text("Sistema não testado", color="grey")
    btn_teste = ft.ElevatedButton(
        "TESTAR CONEXÃO",
        icon=ft.Icons.PLAY_ARROW,
        on_click=realizar_teste_sistema
    )

    return ft.View(
        route="/configuracoes",
        bgcolor="#121417",
        appbar=ft.AppBar(
            title=ft.Text("Configurações"),
            bgcolor="#1e1e1e",
            leading=ft.IconButton(ft.Icons.ARROW_BACK, on_click=voltar)
        ),
        controls=[
            ft.Column([
                # SEÇÃO 1: PERFIL
                ft.Text("CONTA", size=16, weight="bold", color="blue"),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.PERSON),
                    title=ft.Text("Usuário Logado"),
                    subtitle=ft.Text(user_email_logado),
                ),

                # SEÇÃO 2: NOTIFICAÇÕES
                ft.Divider(height=20),
                ft.Text("NOTIFICAÇÕES DE CONSUMO", size=16,
                        weight="bold", color="blue"),
                ft.Row([
                    txt_email_notif,
                    ft.IconButton(
                        ft.Icons.SAVE, on_click=salvar_email_notificacao, icon_color="blue")
                ]),

                # SEÇÃO 3: MÉTODO DE LEITURA
                ft.Divider(height=20),
                ft.Text("MÉTODO DE CAPTURA", size=16,
                        weight="bold", color="blue"),
                ft.Switch(
                    label="Usar Inteligência Artificial (OCR)",
                    value=PreferenciasLeitura.get_modo_ocr(),
                    on_change=lambda e: PreferenciasLeitura.set_modo_ocr(
                        e.control.value)
                ),

                # SEÇÃO 4: DIAGNÓSTICO
                ft.Divider(height=20),
                ft.Text("SAÚDE DO SISTEMA", size=16,
                        weight="bold", color="blue"),
                ft.Container(
                    padding=15,
                    bgcolor="#1e1e1e",
                    border_radius=10,
                    content=ft.Column([
                        ft.Row([status_icon, status_text]),
                        ft.Row([
                            btn_teste,
                            ft.TextButton(
                                "VER DETALHES", on_click=lambda _: page.go("/dashboard_saude"))
                        ], alignment="spaceBetween")
                    ], spacing=10)
                ),

                # SEÇÃO 5: SUPORTE E SAIR
                ft.Divider(height=20),
                ft.ListTile(
                    leading=ft.Icon(ft.Icons.HELP_CENTER, color="orange"),
                    title=ft.Text("Ajuda / Tutorial"),
                    subtitle=ft.Text("Guia de uso do AguaFlow"),
                    on_click=lambda _: page.go("/ajuda")
                ),

                ft.Container(
                    padding=20,
                    content=ft.Column([
                        ft.ElevatedButton(
                            "SAIR DA CONTA",
                            icon=ft.Icons.LOGOUT,
                            bgcolor=ft.Colors.RED_700,
                            color="white",
                            on_click=acao_sair,
                            width=400
                        ),
                        ft.Divider(height=20, color="transparent"),
                        ft.Column([
                            ft.Text("AguaFlow v1.0.5", size=12, color="grey"),
                            ft.Text("Desenvolvido por Grupo 8 - Univesp",
                                    size=10, color="grey"),
                        ], horizontal_alignment="center", width=400)
                    ], horizontal_alignment="center")
                )
            ], scroll=ft.ScrollMode.ADAPTIVE, spacing=10)
        ]
    )
