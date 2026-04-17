import flet as ft
import asyncio
from database.database import Database
from utils.scanner import ScannerAguaFlow
from views import styles as st

def montar_tela_scanner(page: ft.Page):
    lbl_status = ft.Text("Centralize o Hidrômetro", color=st.GREY)
    
    # Campos que começam bloqueados e destravam se o scanner falhar (após 10s)
    txt_unidade = ft.TextField(label="Unidade (Lida via QR)", read_only=True, border_radius=10)
    txt_valor = ft.TextField(label="Valor (m³)", keyboard_type=ft.KeyboardType.NUMBER, border_radius=10, read_only=True)

    async def ao_detectar(unidade, valor, sucesso):
        if unidade: txt_unidade.value = unidade
        if valor: txt_valor.value = valor
        
        if sucesso:
            lbl_status.value = "✅ Captura automática com sucesso!"
            lbl_status.color = "green"
            txt_valor.read_only = False # Garante que pode conferir
        else:
            lbl_status.value = "⚠️ Falha ou Timeout. Insira manualmente."
            lbl_status.color = "orange"
            txt_unidade.read_only = False # Destrava para correção manual
            txt_valor.read_only = False   # Destrava para inserção manual
            txt_unidade.focus()
            
        page.update()

    scanner = ScannerAguaFlow(page, ao_detectar)

    return ft.View(
        route="/scanner",
        controls=[
            ft.AppBar(title=ft.Text("Leitura Inteligente"), bgcolor="#1A1A1A"),
            ft.Container(
                padding=20,
                content=ft.Column([
                    st.criar_mira_scanner(), # A MIRA ANIMADA
                    lbl_status,
                    txt_unidade,
                    txt_valor,
                    ft.ElevatedButton(
                        "ABRIR CÂMERA", 
                        icon=ft.icons.CAMERA_ALT,
                        on_click=lambda _: page.run_task(scanner.iniciar_scan),
                        width=320, height=60, style=st.BTN_SPECIAL
                    ),
                    ft.ElevatedButton(
                        "CONFIRMAR E SALVAR", 
                        on_click=lambda _: page.go("/menu"), # Lógica de save aqui
                        width=320, height=60, style=st.BTN_MAIN
                    )
                ], horizontal_alignment="center", spacing=15)
            )
        ]
    )