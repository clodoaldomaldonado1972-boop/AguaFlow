import flet as ft
from database.database import Database
from .utils.scanner import ScannerAguaFlow

async def montar_tela(page, voltar_ao_menu, on_next):
    registro = Database.buscar_proximo_pendente()
    if not registro: return exibir_conclusao(page, voltar_ao_menu)
    
    id_db, unidade, tipo = registro

    txt_valor = ft.TextField(
        label=f"Unidade: {unidade}",
        max_length=7, # Bloqueio de 7 dígitos
        width=300,
        keyboard_type=ft.KeyboardType.NUMBER,
        input_filter=ft.InputFilter(allow=True, regex_string=r"^\d*$")
    )

    # Função que o scanner chama quando encontra o número
    async def preencher_input(valor_lido):
        txt_valor.value = valor_lido
        page.update()

    # Instancia o módulo de scan separado
    scanner = ScannerAguaFlow(page, ao_detectar_valor=preencher_input)

    async def salvar(e):
        if txt_valor.value:
            Database.registrar_leitura(id_db, txt_valor.value)
            await on_next(None)

    return ft.Column([
        ft.Text("Medição AguaFlow", size=24, weight="bold"),
        txt_valor,
        ft.ElevatedButton(
            "ESCANEAR NÚMEROS", 
            icon=ft.icons.QR_CODE_SCANNER,
            on_click=lambda _: scanner.iniciar_scan(),
            width=300, bgcolor="orange", color="white"
        ),
        ft.ElevatedButton("SALVAR E PRÓXIMO", on_click=salvar, width=300, bgcolor="blue", color="white"),
        ft.TextButton("Voltar", on_click=voltar_ao_menu)
    ], horizontal_alignment="center", spacing=20)