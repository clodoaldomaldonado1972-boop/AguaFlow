import flet as ft
import asyncio
from database.database import Database
from utils.scanner import ScannerAguaFlow
from views import styles as st

def montar_tela_scanner(page: ft.Page):
    """
    Interface de captura que integra a câmara com o preenchimento automático.
    Inclui mira visual e lógica de timeout de 10s.
    """

    # 1. Definição dos Componentes de Texto e Status
    lbl_info = ft.Text("Aguardando captura...", color=st.GREY)

    txt_unidade = ft.TextField(
        label="Unidade (Identificada via QR)",
        read_only=True,
        border_color=st.PRIMARY_BLUE,
        prefix_icon=ft.icons.APARTMENT,
        border_radius=10,
        color="white"
    )

    txt_valor = ft.TextField(
        label="Leitura Atual (m³)",
        keyboard_type=ft.KeyboardType.NUMBER,
        prefix_icon=ft.icons.SPEED,
        border_color=st.PRIMARY_BLUE,
        border_radius=10,
        color="white"
    )

    # 2. Callback: O que acontece quando o motor de OCR termina (ou dá timeout)
    async def ao_receber_dados(unidade, valor, foi_automatico):
        if unidade:
            txt_unidade.value = unidade
        if valor:
            txt_valor.value = str(valor)
        
        if foi_automatico:
            lbl_info.value = "✅ Captura automática realizada!"
            lbl_info.color = "green"
        else:
            # Caso de Timeout ou falha no OCR
            lbl_info.value = "⚠️ Insira o valor manualmente (Timeout/Falha)."
            lbl_info.color = "orange"
        page.update()

    # 3. Instância do Motor do Scanner
    scanner_engine = ScannerAguaFlow(page, ao_receber_dados)

    # 4. Lógica de Salvamento
    async def salvar_leitura(e):
        if not txt_unidade.value or not txt_valor.value:
            page.snack_bar = ft.SnackBar(ft.Text("⚠️ Erro: Capture a leitura primeiro!"))
            page.snack_bar.open = True
            page.update()
            return

        try:
            res = Database.registrar_leitura(
                unidade=txt_unidade.value,
                valor=float(txt_valor.value.replace(',', '.')),
                tipo_leitura="Água"
            )

            if res['sucesso']:
                page.snack_bar = ft.SnackBar(ft.Text("✅ Salvo com sucesso!"), bgcolor="green")
                page.snack_bar.open = True
                page.update()
                await asyncio.sleep(1)
                page.go("/menu")
            else:
                page.snack_bar = ft.SnackBar(ft.Text(f"Erro: {res['mensagem']}"))
                page.snack_bar.open = True
        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("Erro: Valor numérico inválido!"))
        page.update()

    # --- LAYOUT DA VIEW ---
    return ft.View(
        route="/scanner",
        appbar=ft.AppBar(
            title=ft.Text("Scanner AguaFlow"),
            bgcolor=st.PRIMARY_BLUE,
            color="white",
            leading=ft.IconButton(ft.icons.ARROW_BACK, icon_color="white", on_click=lambda _: page.go("/menu"))
        ),
        bgcolor=st.BG_DARK,
        controls=[
            ft.Container(
                padding=20,
                content=ft.Column([
                    ft.Text("Leitura Automática", style=st.TEXT_TITLE),
                    ft.Text("Posicione o hidrómetro no quadro abaixo", color=st.GREY),
                    
                    # MIRA VISUAL VINDA DO STYLES.PY
                    st.criar_mira_scanner(), 

                    lbl_info,
                    ft.Divider(height=10, color="transparent"),

                    txt_unidade,
                    txt_valor,

                    ft.Divider(height=10, color="transparent"),

                    ft.ElevatedButton(
                        "ACIONAR CÂMARA",
                        icon=ft.icons.CAMERA_ALT,
                        on_click=lambda _: page.run_task(scanner_engine.iniciar_scan),
                        bgcolor=ft.colors.ORANGE_700,
                        color="white",
                        width=320,
                        height=60
                    ),

                    ft.ElevatedButton(
                        "CONFIRMAR E SALVAR",
                        icon=ft.icons.SAVE,
                        on_click=salvar_leitura,
                        bgcolor=st.PRIMARY_BLUE,
                        color="white",
                        width=320,
                        height=60
                    ),
                    
                    ft.TextButton("Voltar ao Menu", on_click=lambda _: page.go("/menu"))
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15)
            )
        ]
    )