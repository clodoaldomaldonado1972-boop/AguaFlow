import flet as ft
# --- IMPORTS CORRIGIDOS PARA A NOVA ESTRUTURA ---
from database.database import Database
from utils.scanner import ScannerAguaFlow  # Scanner movido para a pasta utils/
from views import styles as st  # Uso dos estilos unificados


def montar_tela_scanner(page: ft.Page):
    """
    Interface de captura que integra a câmera com o preenchimento automático[cite: 18].
    """

    # 1. Campos da Interface usando estilos padronizados[cite: 18]
    txt_unidade = ft.TextField(
        label="Unidade (Identificada via QR)",
        read_only=True,
        border_color=st.PRIMARY_BLUE,
        prefix_icon=ft.icons.APARTMENT,
        border_radius=10
    )

    txt_valor = ft.TextField(
        label="Leitura Atual (m³)",
        keyboard_type=ft.KeyboardType.NUMBER,
        prefix_icon=ft.icons.SPEED,
        border_color=st.PRIMARY_BLUE,
        border_radius=10
    )

    # 2. Função de atualização (Callback)[cite: 18]
    async def ao_receber_dados(unidade, valor, foi_automatico):
        """Atualiza os campos assim que o motor de visão processa a foto[cite: 18]."""
        txt_unidade.value = unidade
        txt_valor.value = valor if valor else ""

        if not foi_automatico:
            txt_valor.focus()

        page.update()

    # 3. Instancia o Scanner (passando a função de callback)[cite: 18]
    scanner_engine = ScannerAguaFlow(page, ao_receber_dados)

    # 4. Funções de Ação[cite: 18]
    def salvar_leitura(e):
        if txt_unidade.value and txt_valor.value:
            # Busca o tipo de filtro (Água/Gás) definido na sessão da página
            tipo = getattr(page, "filtro_leitura", "Água")
            res = Database.registrar_leitura(
                txt_unidade.value, txt_valor.value, tipo)

            if res.get('sucesso'):
                page.snack_bar = ft.SnackBar(
                    ft.Text("Leitura salva e na fila de envio!"), bgcolor="green")
                page.snack_bar.open = True
                # Limpa campos para a próxima leitura
                txt_unidade.value = ""
                txt_valor.value = ""
                page.update()
        else:
            page.snack_bar = ft.SnackBar(
                ft.Text("Por favor, preencha todos os campos."), bgcolor="red")
            page.snack_bar.open = True
            page.update()

    # 5. Layout da View[cite: 18]
    return ft.View(
        route="/scanner",
        bgcolor=st.BG_DARK,
        appbar=ft.AppBar(
            title=ft.Text("Scanner AguaFlow"),
            bgcolor="#1e1e1e",
            leading=ft.IconButton(ft.icons.ARROW_BACK,
                                  on_click=lambda _: page.go("/menu"))
        ),
        controls=[
            ft.Container(
                padding=20,
                content=ft.Column([
                    # Estilo do styles.py[cite: 9]
                    ft.Text("Registro de Consumo", style=st.TEXT_TITLE),
                    ft.Text(
                        "Aponte a câmera para o QR Code e o visor do hidrômetro", color=st.GREY),
                    ft.Divider(height=20, color="transparent"),

                    txt_unidade,
                    txt_valor,

                    ft.Divider(height=20, color="transparent"),

                    # Botão Flutuante de Escaneamento[cite: 18]
                    ft.ElevatedButton(
                        "ESCANEAR HIDRÔMETRO",
                        icon=ft.icons.CAMERA_ALT,
                        on_click=lambda _: scanner_engine.iniciar_scan(),
                        style=st.BTN_SPECIAL,  # Laranja para destaque[cite: 9]
                        width=320,
                        height=60
                    ),

                    ft.ElevatedButton(
                        "SALVAR MANUALMENTE",
                        icon=ft.icons.SAVE,
                        on_click=salvar_leitura,
                        style=st.BTN_MAIN,  # Azul padrão[cite: 9]
                        width=320,
                        height=60
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
            )
        ]
    )
