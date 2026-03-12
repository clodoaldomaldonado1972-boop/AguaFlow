import flet as ft
import database as db
import camera_utils
import asyncio

COR_PRIMARIA = "blue"
COR_ALERTA = "orange"


async def montar_tela(page: ft.Page, voltar_menu):
    processando = False
    page.overlay.clear()
    page.update()

    unidade = db.buscar_proximo_pendente()

    if not unidade:
        return ft.Container(
            expand=True, bgcolor="#1A1C1E", alignment=ft.Alignment(0, 0),
            content=ft.Column([
                ft.Icon(ft.icons.CHECK_CIRCLE, color="green", size=80),
                ft.Text("Todas as medições concluídas!",
                        size=24, color="white"),
                ft.ElevatedButton("Voltar ao Menu",
                                  on_click=lambda _: voltar_menu())
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    id_db, nome_unidade, leitura_anterior = unidade[0], unidade[1], unidade[2]
    texto_consumo = ft.Text("Consumo: 0.00 m³", size=18,
                            color=COR_PRIMARIA, weight="bold")

    def calcular_ao_digitar(e):
        try:
            input_valor.error_text = None
            if input_valor.value:
                val_limpo = input_valor.value.replace(",", ".")
                atual = float(val_limpo)
                consumo = atual - leitura_anterior
                texto_consumo.value = f"Consumo: {consumo:.2f} m³"
                texto_consumo.color = COR_ALERTA if consumo > 20 or consumo < 0 else COR_PRIMARIA
            else:
                texto_consumo.value = "Consumo: 0.00 m³"
        except ValueError:
            texto_consumo.value = "Consumo: ---"
        page.update()

    input_valor = ft.TextField(
        label="Leitura Atual (m³)",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=250, color="white",
        on_change=calcular_ao_digitar,
    )

    # Callback disparado pelo camera_utils
    async def ao_concluir_ocr(id_qr, valor_ocr):
        if id_qr and str(id_qr).strip() != str(nome_unidade).strip():
            input_valor.error_text = f"Aviso: QR Code ({id_qr}) não confere!"
        if valor_ocr:
            input_valor.value = str(valor_ocr).strip()
            calcular_ao_digitar(None)
        page.update()

    # Inicialização simplificada
    seletor_camera = await camera_utils.inicializar_camera(page, ao_concluir_ocr)

    async def acionar_camera(e):
        await seletor_camera.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE)

    return ft.Container(
        expand=True, bgcolor="#1A1C1E", padding=30,
        content=ft.Column(
            controls=[
                ft.Text(f"Unidade: {nome_unidade}",
                        size=28, weight="bold", color="blue"),
                ft.Text(f"Anterior: {leitura_anterior:.2f} m³",
                        size=18, color="white70"),
                ft.Divider(color="white10"),
                ft.Row([
                    input_valor,
                    ft.IconButton(ft.icons.CAMERA_ALT,
                                  icon_color="blue", on_click=acionar_camera)
                ], alignment=ft.MainAxisAlignment.CENTER),
                texto_consumo,
                ft.Row([
                    ft.FilledButton("SALVAR", icon=ft.icons.SAVE,
                                    on_click=lambda _: None, width=150),
                    ft.IconButton(icon=ft.icons.SKIP_NEXT,
                                  on_click=lambda _: None)
                ], alignment=ft.MainAxisAlignment.CENTER),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20
        )
    )
