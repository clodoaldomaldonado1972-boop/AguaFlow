import flet as ft
import database as db
import camera_utils
import asyncio


async def montar_tela(page: ft.Page, voltar_menu):
    seletor_camera = None
    processando = False

    page.overlay.clear()
    page.update()

    # Busca a próxima unidade pendente no banco de dados
    unidade = db.buscar_proximo_pendente()

    if not unidade:
        return ft.Container(
            expand=True, bgcolor="#1A1C1E", alignment=ft.Alignment(0, 0),
            content=ft.Column([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color="green", size=80),
                ft.Text("Todas as medições concluídas!",
                        size=24, color="white"),
                ft.ElevatedButton("Voltar ao Menu", on_click=voltar_menu)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    id_db, nome_unidade, leitura_anterior = unidade[0], unidade[1], unidade[2]

    texto_consumo = ft.Text("Consumo: 0.00 m³", size=18,
                            color="blue", weight="bold")

    # Função para calcular o consumo em tempo real
    def calcular_ao_digitar(e):
        try:
            input_valor.error_text = None
            if input_valor.value:
                val_limpo = input_valor.value.replace(",", ".")
                consumo = float(val_limpo) - leitura_anterior
                texto_consumo.value = f"Consumo: {consumo:.2f} m³"
                # Alerta visual se o consumo for muito alto ou negativo
                texto_consumo.color = "orange" if consumo > 20 or consumo < 0 else "blue"
            page.update()
        except:
            pass

    input_valor = ft.TextField(
        label="Leitura Atual (m³)",
        keyboard_type=ft.KeyboardType.NUMBER,
        width=250, color="white",
        on_change=calcular_ao_digitar,
    )

    # Função para salvar no banco de dados
    async def salvar_leitura(e):
        nonlocal processando
        if processando or not input_valor.value:
            input_valor.error_text = "Digite um valor"
            page.update()
            return
        try:
            processando = True
            valor = float(input_valor.value.replace(",", "."))
            db.registrar_leitura(id_db, valor)
            # Recarrega a tela com a próxima unidade
            await voltar_menu(recarregar_medicao=True)
        except Exception as ex:
            processando = False
            print(f"Erro ao salvar: {ex}")
            page.update()

    # Callback que recebe o valor detectado pela câmera/OCR
    async def ao_concluir_ocr(id_qr, valor_ocr):
        if valor_ocr:
            input_valor.value = str(valor_ocr)
            calcular_ao_digitar(None)
        page.update()

    # Inicializa o componente de câmera
    seletor_camera = await camera_utils.inicializar_camera(page, ao_concluir_ocr)

    async def acionar_camera(e):
        nonlocal seletor_camera
        if seletor_camera is None:
            seletor_camera = await camera_utils.inicializar_camera(page, ao_concluir_ocr)

        try:
            # Garante que o seletor esteja na página antes de abrir
            if seletor_camera not in page.overlay:
                page.overlay.append(seletor_camera)
            page.update()

            # Abre a câmera/galeria
            seletor_camera.pick_files(
                allow_multiple=False,
                file_type=ft.FilePickerFileType.IMAGE
            )
        except Exception as ex:
            print(f"Erro Camera: {ex}")

    async def pular_unidade(e):
        try:
            # Forçamos o recarregamento da tela chamando o menu novamente
            await voltar_menu(recarregar_medicao=True)
        except Exception as ex:
            print(f"Erro ao pular: {ex}")

    # --- INTERFACE VISUAL REFORMULADA ---
    return ft.Container(
        expand=True, bgcolor="#1A1C1E", padding=30,
        content=ft.Column(
            controls=[
                ft.Text(f"Unidade: {nome_unidade}",
                        size=28, weight="bold", color="blue"),
                ft.Divider(color="white10"),

                # FOCO 1: BOTÃO DE CÂMERA (Ação principal sugerida)
                ft.ElevatedButton(
                    "ESCANEAR HIDRÔMETRO",
                    icon=ft.Icons.CAMERA_ALT,
                    on_click=acionar_camera,
                    style=ft.ButtonStyle(
                        color="white",
                        bgcolor="blue",
                        shape=ft.RoundedRectangleBorder(radius=10)
                    ),
                    height=60, width=300
                ),

                ft.Text("OU AJUSTE MANUALMENTE:", size=14, color="white54"),

                # FOCO 2: ENTRADA MANUAL (Para correção ou falha do OCR)
                ft.Row([
                    input_valor,
                ], alignment="center"),

                texto_consumo,

                # AÇÕES DE RODAPÉ
                ft.Row([
                    ft.FilledButton(
                        "SALVAR LEITURA",
                        icon=ft.Icons.SAVE,
                        on_click=salvar_leitura,
                        width=180
                    ),
                    ft.IconButton(
                        icon=ft.Icons.SKIP_NEXT,
                        icon_color="white54",
                        tooltip="Pular unidade",
                        on_click=pular_unidade
                    )
                ], alignment="center"),
            ],
            horizontal_alignment="center", spacing=25
        )
    )
