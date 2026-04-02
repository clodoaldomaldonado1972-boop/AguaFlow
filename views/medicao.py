import flet as ft
from database.database import Database
from .utils.scanner import ScannerAguaFlow

# MUDANÇA: O nome da função agora é montar_tela_medicao para bater com o main.py


async def montar_tela_medicao(page: ft.Page):

    # Funções de navegação internas
    def voltar_ao_menu(e):
        page.go("/menu")

    async def on_next(e):
        # Recarrega a tela para buscar o próximo pendente
        page.go("/medicao")

    # 1. Busca o próximo apartamento pendente no SQLite
    registro = Database.buscar_proximo_pendente()

    # Se não houver mais nada para ler, exibe mensagem de conclusão
    if not registro:
        return ft.Container(
            padding=40,
            content=ft.Column([
                ft.Icon(ft.icons.CHECK_CIRCLE, color="green", size=80),
                ft.Text("Concluído!", size=28, weight="bold"),
                ft.Text("Todas as leituras foram realizadas.",
                        textAlign="center"),
                ft.ElevatedButton("Voltar ao Menu",
                                  on_click=voltar_ao_menu, width=200)
            ], horizontal_alignment="center", spacing=20)
        )

    id_db, unidade, tipo = registro

    # 2. Configuração do Campo de Texto
    txt_valor = ft.TextField(
        label=f"Unidade: {unidade}",
        width=300,
        hint_text="00000,00",
        max_length=8,
        keyboard_type=ft.KeyboardType.NUMBER,
        input_filter=ft.InputFilter(
            allow=True,
            regex_string=r"^[0-9,.]*$",
            replacement_string=""
        ),
        counter_text="Máximo 7 dígitos + separador",
    )

    # 3. Lógica do Scanner OCR
    async def preencher_input(valor_lido):
        txt_valor.value = str(valor_lido)
        page.update()

    scanner = ScannerAguaFlow(page, ao_detectar_valor=preencher_input)

    # 4. Lógica de Salvamento
    async def salvar(e):
        if not txt_valor.value:
            page.snack_bar = ft.SnackBar(
                ft.Text("❌ Insira um valor!"), bgcolor="red")
            page.snack_bar.open = True
            page.update()
            return

        resultado = Database.registrar_leitura(id_db, txt_valor.value)

        if resultado['sucesso']:
            page.snack_bar = ft.SnackBar(
                ft.Text(resultado['mensagem']), bgcolor="green")
            page.snack_bar.open = True
            await on_next(None)
        else:
            page.snack_bar = ft.SnackBar(
                ft.Text(resultado['mensagem']), bgcolor="red")
            page.snack_bar.open = True

        page.update()

    # 5. Layout da Tela
    return ft.Container(
        padding=20,
        content=ft.Column([
            ft.Text("Medição em Campo", size=24, weight="bold"),
            ft.Text(f"Vivere Prudente - Unidade {unidade}", color="blue"),
            ft.Divider(height=10, color="transparent"),
            txt_valor,
            ft.ElevatedButton(
                "ESCANEAR COM CÂMERA",
                icon=ft.icons.CAMERA_ALT,
                on_click=lambda _: page.run_task(scanner.iniciar_scan),
                width=300, style=st.BTN_MAIN, color="white"
            ),
            ft.ElevatedButton(
                "SALVAR E PRÓXIMO",
                icon=ft.icons.SAVE,
                on_click=salvar,
                width=300, style=st.BTN_SPECIAL, color="white"
            ),
            ft.TextButton(
                "Sair da Medição",
                icon=ft.icons.EXIT_TO_APP,
                on_click=voltar_ao_menu,
                style=ft.ButtonStyle(color="grey")
            )
        ], horizontal_alignment="center", spacing=15)
    )
