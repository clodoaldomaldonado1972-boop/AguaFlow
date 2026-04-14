import flet as ft
from views import styles as st
from utils.suporte_helper import SuporteHelper

def montar_tela_ajuda(page, on_back_click):
    user_email = getattr(page, "user_email", "Usuário")

    return ft.View(
        route="/ajuda",
        bgcolor=st.BG_DARK,
        controls=[
            ft.AppBar(
                title=ft.Text("Manual do Usuário"),
                leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=on_back_click),
                bgcolor=ft.colors.BLUE_900
            ),
            ft.ListView(
                expand=True,
                padding=20,
                spacing=15,
                controls=[
                    ft.Text("Como usar o AguaFlow", size=24, weight="bold", color=st.PRIMARY_BLUE),
                    
                    ft.ExpansionTile(
                        title=ft.Text("1. Realizar Medição"),
                        subtitle=ft.Text("Passo a passo para usar o scanner OCR"),
                        controls=[
                            ft.ListTile(title=ft.Text("Aponte a câmera para o hidrômetro.")),
                            ft.ListTile(title=ft.Text("Garanta que os números estejam legíveis.")),
                            ft.ListTile(title=ft.Text("Confirme o valor lido pela IA.")),
                        ],
                    ),
                    
                    ft.ExpansionTile(
                        title=ft.Text("2. Monitoramento e Grafana"),
                        subtitle=ft.Text("Entenda os gráficos de consumo"),
                        controls=[
                            ft.ListTile(title=ft.Text("Acesse 'Configurações' para abrir o Grafana.")),
                            ft.ListTile(title=ft.Text("Lá você verá o histórico de telemetria.")),
                        ],
                    ),
                    
                    ft.Divider(height=20),
                    
                    ft.Text("Ainda precisa de ajuda?", size=16, weight="bold"),
                    
                    ft.ElevatedButton(
                        "FALAR COM SUPORTE (WHATSAPP)",
                        icon=ft.icons.CHAT,
                        bgcolor=ft.colors.GREEN_700,
                        color="white",
                        on_click=lambda _: SuporteHelper.abrir_whatsapp_suporte(page, user_email)
                    ),
                    
                    ft.TextButton(
                        "BAIXAR MANUAL EM PDF",
                        icon=ft.icons.PICTURE_AS_PDF,
                        on_click=lambda _: SuporteHelper.abrir_manual_externo(page)
                    ),
                ]
            )
        ]
    )