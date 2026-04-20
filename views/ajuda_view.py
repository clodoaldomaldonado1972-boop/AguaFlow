import flet as ft
from views import styles as st # Mantém a padronização visual
from utils.suporte_helper import SuporteHelper 

def montar_tela_ajuda(page: ft.Page, voltar):
    # Recupera o e-mail do utilizador para personalizar o suporte
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

                    # --- MANUAL INTERATIVO ---
                    ft.ExpansionTile(
                        title=ft.Text("Como realizar uma medição?"),
                        leading=ft.Icon(ft.icons.CAMERA_ALT, color="green"),
                        collapsed_text_color="white",
                        controls=[
                            ft.ListTile(title=ft.Text("1. Aceda a 'Realizar Leituras' no menu.")),
                            ft.ListTile(title=ft.Text("2. Aponte a câmara para o medidor.")),
                            ft.ListTile(title=ft.Text("3. Garanta boa luz para o OCR (leitor automático).")),
                            ft.ListTile(title=ft.Text("4. Confirme o valor e clique em Salvar.")),
                        ]
                    ),

                    ft.ExpansionTile(
                        title=ft.Text("Dificuldades com o Scanner?"),
                        leading=ft.Icon(ft.icons.ERRORS_OUTLINED, color="orange"),
                        controls=[
                            ft.ListTile(title=ft.Text("• Limpe a lente da câmara do telemóvel.")),
                            ft.ListTile(title=ft.Text("• Evite reflexos diretos no visor do medidor.")),
                            ft.ListTile(title=ft.Text("• Se falhar, utilize o ícone de 'Lápis' para introdução manual.")),
                        ]
                    ),

                    ft.Divider(height=30, color="white10"),
                    
                    # --- BOTÕES DE AÇÃO EXTERNA ---
                    ft.Text("Ainda precisa de assistência?", size=16, weight="bold", color="white"),
                    
                    ft.ElevatedButton(
                        "ABRIR MANUAL TÉCNICO (PDF)",
                        icon=ft.icons.PICTURE_AS_PDF,
                        on_click=lambda _: SuporteHelper.abrir_manual(page),
                        width=400,
                        height=50,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                    ),
                    
                    ft.Container(height=5),

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
                    
                    # Botão de Voltar customizado
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
                scroll=ft.ScrollMode.ADAPTIVE 
                )
            )
        ]
    )