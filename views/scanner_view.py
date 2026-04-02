import flet as ft
from database import Database
from .utils.scanner import ScannerAguaFlow

def ScannerView(page: ft.Page):
    # 1. Campos da Interface
    txt_unidade = ft.TextField(
        label="Unidade (Identificada via QR)", 
        read_only=True, 
        border_color="blue",
        prefix_icon=ft.icons.APARTMENT
    )
    
    txt_valor = ft.TextField(
        label="Leitura Atual (m³)", 
        keyboard_type=ft.KeyboardType.NUMBER,
        prefix_icon=ft.icons.SPEED
    )

    # 2. Função de atualização (Callback)
    async def ao_receber_dados(unidade, valor, foi_automatico):
        txt_unidade.value = unidade
        txt_valor.value = valor if valor else ""
        
        if not foi_automatico:
            txt_valor.focus()
            
        page.update()

    # 3. Instancia o Scanner (passando a função acima)
    scanner_engine = ScannerAguaFlow(page, ao_receber_dados)

    # 4. Botão de Ação
    btn_scan = ft.FloatingActionButton(
        icon=ft.icons.CAMERA_ALT,
        text="Escanear Hidrômetro",
        on_click=lambda _: page.run_task(scanner_engine.iniciar_scan)
    )

    # Retorna o layout da página
    return ft.Column([
        ft.Text("Registro de Consumo", size=24, weight="bold"),
        ft.Divider(),
        txt_unidade,
        txt_valor,
        ft.Row([btn_scan], alignment=ft.MainAxisAlignment.CENTER),
        ft.ElevatedButton(
            "Salvar Manualmente", 
            on_click=lambda _: Database.registrar_leitura(txt_unidade.value, txt_valor.value)
        )
    ], spacing=20)