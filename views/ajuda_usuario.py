import flet as ft
from views import styles as st # Importa os estilos padronizados do AguaFlow
from utils.suporte_helper import SuporteHelper # Classe que gerencia PDF e WhatsApp

def montar_tela_ajuda(page: ft.Page, voltar):
    # Recupera o e-mail do usuário logado para personalizar o atendimento no WhatsApp
    user_email = getattr(page, "user_email", "Usuário não identificado")
    
    return ft.View(
        route="/ajuda",
        bgcolor=st.BG_DARK, # Usa o fundo escuro padrão
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
                    # Título de Boas-vindas
                    ft.Text("Guia Rápido AguaFlow", style=st.TEXT_TITLE, color=st.PRIMARY_BLUE),
                    ft.Text(f"Sessão: {user_email}", size=12, color="grey"),
                    ft.Divider(height=20, color="transparent"),

                    # --- SEÇÃO 1: MANUAL INTERATIVO (EXPANSION TILES) ---
                    ft.ExpansionTile(
                        title=ft.Text("Como realizar uma medição?"),
                        leading=ft.Icon(ft.icons.CAMERA_ALT, color="green"),
                        collapsed_text_color="white",
                        controls=[
                            ft.ListTile(title=ft.Text("1. Clique em 'Realizar Leituras' no menu.")),
                            ft.ListTile(title=ft.Text("2. Aponte a câmera para o hidrômetro/medidor.")),
                            ft.ListTile(title=ft.Text("3. Garanta boa iluminação para o OCR funcionar.")),
                            ft.ListTile(title=ft.Text("4. Confirme os números e clique em Salvar.")),
                        ]
                    ),

                    ft.ExpansionTile(
                        title=ft.Text("Problemas com o Scanner (OCR)?"),
                        leading=ft.Icon(ft.icons.ERROR_OUTLINED, color="orange"),
                        controls=[
                            ft.ListTile(title=ft.Text("• Limpe a lente da câmera.")),
                            ft.ListTile(title=ft.Text("• Evite reflexos de luz direta no visor.")),
                            ft.ListTile(title=ft.Text("• Se falhar, use o ícone de 'Lápis' para digitar manual.")),
                        ]
                    ),

                    ft.Divider(height=30, color="white10"),
                    
                    # --- SEÇÃO 2: BOTÕES DE SUPORTE EXTERNO ---
                    ft.Text("Ainda precisa de ajuda técnica?", size=16, weight="bold", color="white"),
                    
                    # Botão para abrir o Manual Técnico (PDF)
                    ft.ElevatedButton(
                        "ABRIR MANUAL COMPLETO (PDF)",
                        icon=ft.icons.PICTURE_AS_PDF,
                        on_click=lambda _: SuporteHelper.abrir_manual(page),
                        width=400,
                        height=50,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                    ),
                    
                    ft.Container(height=5),

                    # Botão para contato direto via WhatsApp
                    ft.ElevatedButton(
                        "FALAR COM SUPORTE (WHATSAPP)",
                        icon=ft.icons.CHAT,
                        bgcolor=ft.colors.GREEN_700,
                        color="white",
                        on_click=lambda _: SuporteHelper.abrir_whatsapp_suporte(page, user_email),
                        width=400,
                        height=50,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                    ),

                    ft.Divider(height=30, color="transparent"),
                    
                    # Botão de retorno
                    ft.OutlinedButton(
                        "VOLTAR AO MENU",
                        icon=ft.icons.CHECK,
                        on_click=voltar,
                        width=400,
                        height=50,
                        style=ft.ButtonStyle(
                            color=st.PRIMARY_BLUE,
                            side=ft.BorderSide(1, st.PRIMARY_BLUE)
                        )
                    )
                ], 
                spacing=10, 
                scroll=ft.ScrollMode.ADAPTIVE # Permite rolar a tela em celulares pequenos
                )
            )
        ]
    )