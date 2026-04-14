import flet as ft
from utils.suporte_helper import SuporteHelper # Importa para usar o Manual PDF e Whats

def montar_tela_ajuda(page, voltar):
    user_email = getattr(page, "user_email", "Usuário")
    
    return ft.View(
        route="/ajuda",
        bgcolor="#121417",
        appbar=ft.AppBar(
            title=ft.Text("Central de Ajuda & Suporte"),
            bgcolor="#1e1e1e",
            leading=ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=voltar)
        ),
        controls=[
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("Guia Rápido AguaFlow", size=22, weight="bold", color="blue"),
                    ft.Divider(height=20),

                    # Seção 1: Operacional
                    ft.ExpansionTile(
                        title=ft.Text("Como realizar uma medição?"),
                        leading=ft.Icon(ft.icons.CAMERA_ALT, color="green"),
                        controls=[
                            ft.ListTile(title=ft.Text("1. Clique em 'Realizar Leituras' no menu.")),
                            ft.ListTile(title=ft.Text("2. Aponte a câmera para o hidrômetro.")),
                            ft.ListTile(title=ft.Text("3. Confirme os números e clique em Salvar.")),
                        ]
                    ),

                    # Seção 2: Solução de Problemas
                    ft.ExpansionTile(
                        title=ft.Text("Problemas com o Scanner (OCR)?"),
                        leading=ft.Icon(ft.icons.BUG_REPORT, color="orange"),
                        controls=[
                            ft.ListTile(title=ft.Text("• Limpe o visor do hidrômetro.")),
                            ft.ListTile(title=ft.Text("• Evite reflexos de luz direta.")),
                            ft.ListTile(title=ft.Text("• Se falhar, use o ícone de 'Lápis' para digitar manual.")),
                        ]
                    ),

                    ft.Divider(height=20),
                    
                    # --- NOVOS BOTÕES DE SUPORTE EXTERNO ---
                    ft.Text("Ainda precisa de ajuda técnica?", size=16, weight="bold"),
                    
                    ft.ElevatedButton(
                        "ABRIR MANUAL COMPLETO (PDF)",
                        icon=ft.icons.PICTURE_AS_PDF,
                        on_click=lambda _: SuporteHelper.abrir_manual(page),
                        width=400
                    ),
                    
                    ft.ElevatedButton(
                        "FALAR COM SUPORTE (WHATSAPP)",
                        icon=ft.icons.CHAT,
                        bgcolor=ft.colors.GREEN_700,
                        color="white",
                        on_click=lambda _: SuporteHelper.abrir_whatsapp_suporte(page, user_email),
                        width=400
                    ),

                    ft.Divider(height=20),
                    ft.ElevatedButton(
                        "VOLTAR AO MENU",
                        icon=ft.icons.CHECK,
                        on_click=voltar,
                        width=400
                    )
                ], spacing=10, scroll=ft.ScrollMode.ADAPTIVE)
            )
        ]
    )