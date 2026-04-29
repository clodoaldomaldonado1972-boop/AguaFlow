import flet as ft
from views import styles as st  # Mantém a padronização visual do AguaFlow
from utils.suporte_helper import SuporteHelper 

def montar_tela_ajuda(page: ft.Page, voltar):
    """
    Interface Unificada de Ajuda e Suporte - Versão 1.1.2
    IHC: Centraliza manuais e contato direto com suporte técnico.
    """
    # Recupera o e-mail do utilizador logado para personalizar o atendimento
    user_email = getattr(page, "user_email", "Utilizador não identificado")
    
    return ft.View(
        route="/ajuda",
        bgcolor=st.BG_DARK,
        appbar=ft.AppBar(
            title=ft.Text("Central de Ajuda & Suporte"),
            bgcolor=ft.colors.BLUE_900,
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=voltar),
            center_title=True
        ),
        controls=[
            ft.Container(
                padding=20,
                content=ft.Column([
                    # Cabeçalho da página
                    ft.Text("Guia Rápido AguaFlow", style=st.TEXT_TITLE, color=st.PRIMARY_BLUE),
                    ft.Text(f"Sessão ativa: {user_email}", size=12, color="grey"),
                    ft.Divider(height=20, color="transparent"),

                    # --- SEÇÃO 1: MANUAL INTERATIVO (FAQ) ---
                    ft.Text("Perguntas Frequentes", size=18, weight="bold", color="white"),
                    
                    ft.ExpansionTile(
                        title=ft.Text("Como realizar uma medição?"),
                        leading=ft.Icon(ft.icons.CAMERA_ALT, color="green"),
                        controls=[
                            ft.ListTile(title=ft.Text("Abra o scanner, aponte para os números pretos do hidrômetro e aguarde o processamento automático."))
                        ]
                    ),
                    
                    ft.ExpansionTile(
                        title=ft.Text("O que fazer se o OCR falhar?"),
                        leading=ft.Icon(ft.icons.REPLAY_CIRCLE_FILLED, color="orange"),
                        controls=[
                            ft.ListTile(title=ft.Text("Certifique-se de que há luz suficiente. Se persistir, pode digitar o valor manualmente no campo de leitura."))
                        ]
                    ),

                    ft.ExpansionTile(
                        title=ft.Text("Como funciona a sincronização?"),
                        leading=ft.Icon(ft.icons.CLOUD_SYNC, color=st.PRIMARY_BLUE),
                        controls=[
                            ft.ListTile(title=ft.Text("Após terminar as leituras, clique no ícone da nuvem. O sistema enviará os dados e gerará os relatórios automaticamente."))
                        ]
                    ),

                    ft.Divider(height=30, color="transparent"),

                    # --- SEÇÃO 2: AÇÕES DE SUPORTE EXTERNO ---
                    ft.Text("Ainda precisa de ajuda?", size=18, weight="bold", color="white"),
                    ft.Container(height=10),

                    # Botão para abrir o Manual Completo (Google Docs)
                    ft.ElevatedButton(
                        "ACEDER MANUAL COMPLETO (PDF/WEB)",
                        icon=ft.icons.DESCRIPTION,
                        bgcolor=ft.colors.BLUE_GREY_700,
                        color="white",
                        on_click=lambda _: SuporteHelper.abrir_manual(page),
                        width=400,
                        height=50,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                    ),
                    
                    ft.Container(height=5),

                    # Botão para contato direto via WhatsApp
                    ft.ElevatedButton(
                        "CONTACTAR SUPORTE (WHATSAPP)",
                        icon=ft.icons.CHAT,
                        bgcolor=ft.colors.GREEN_700,
                        color="white",
                        on_click=lambda _: SuporteHelper.abrir_whatsapp_suporte(page, user_email),
                        width=400,
                        height=50,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                    ),

                    ft.Divider(height=30, color="transparent"),
                    
                    # Botão de retorno ao menu principal
                    ft.OutlinedButton(
                        "VOLTAR AO MENU",
                        icon=ft.icons.HOME,
                        on_click=voltar,
                        width=400,
                        height=50,
                        style=ft.ButtonStyle(
                            color=st.PRIMARY_BLUE,
                            side=ft.BorderSide(1, st.PRIMARY_BLUE),
                            shape=ft.RoundedRectangleBorder(radius=10)
                        )
                    )
                ], 
                spacing=10, 
                scroll=ft.ScrollMode.ADAPTIVE # Essencial para scroll em Android
                )
            )
        ]
    )