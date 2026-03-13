import flet as ft
import database as db
import camera_utils
import asyncio

async def montar_tela(page: ft.Page, voltar_menu):
    # Declaramos as variáveis no escopo da função para acesso via 'nonlocal'.
    seletor_camera = None
    processando = False

    # Limpeza garante que seletores antigos não fiquem presos.
    page.overlay.clear()
    page.update()

    # Busca a próxima unidade conforme a sequência do condomínio.
    unidade = db.buscar_proximo_pendente()

    if not unidade:
        return ft.Container(
            expand=True, bgcolor="#1A1C1E", alignment=ft.Alignment(0, 0),
            content=ft.Column([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color="green", size=80),
                ft.Text("Todas as medições concluídas!",
                        size=24, color="white"),
                ft.ElevatedButton(
                    "Voltar ao Menu",
                    on_click=lambda _: page.run_task(voltar_menu)
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    id_db, nome_unidade, leitura_anterior = unidade[0], unidade[1], unidade[2]
    texto_consumo = ft.Text("Consumo: 0.00 m³", size=18,
                            color="blue", weight="bold")

    def calcular_ao_digitar(e):
        """Calcula o consumo em tempo real."""
        try:
            input_valor.error_text = None
            if input_valor.value:
                val_limpo = input_valor.value.replace(",", ".")
                consumo = float(val_limpo) - leitura_anterior
                texto_consumo.value = f"Consumo: {consumo:.2f} m³"
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

    async def salvar_leitura(e):
        """Persiste os dados no SQLite."""
        nonlocal processando
        if processando or not input_valor.value:
            input_valor.error_text = "Digite um valor"
            page.update()
            return
        try:
            processando = True
            valor = float(input_valor.value.replace(",", "."))
            db.registrar_leitura(id_db, valor)
            await voltar_menu(recarregar_medicao=True)
        except Exception as ex:
            processando = False
            print(f"Erro ao salvar: {ex}")

    async def ao_concluir_ocr(id_qr, valor_ocr):
        """Callback após o OCR da imagem."""
        if valor_ocr:
            input_valor.value = str(valor_ocr)
            calcular_ao_digitar(None)
        page.update() # Corrigido: Removido await e _async

    # Inicialização do FilePicker.
    seletor_camera = await camera_utils.inicializar_camera(page, ao_concluir_ocr)

    async def acionar_camera(e):
        """Gerencia o acionamento da câmera."""
        nonlocal seletor_camera
        if seletor_camera is None:
            seletor_camera = await camera_utils.inicializar_camera(page, ao_concluir_ocr)

        if seletor_camera is not None:
            try:
                if seletor_camera not in page.overlay:
                    page.overlay.append(seletor_camera)
                seletor_camera.page = page
                page.update() # Corrigido: Removido await e _async
                await seletor_camera.pick_files(
                    allow_multiple=False,
                    file_type=ft.FilePickerFileType.IMAGE
                )
            except Exception as ex:
                print(f"Erro interno no seletor: {ex}")
        else:
            page.snack_bar = ft.SnackBar(ft.Text("Erro: Câmera não inicializada."))
            page.snack_bar.open = True
            page.update()

    async def pular_unidade(e):
        await voltar_menu(recarregar_medicao=True)

    return ft.Container(
        expand=True, bgcolor="#1A1C1E", padding=30,
        content=ft.Column(
            controls=[
                ft.Text(f"Unidade: {nome_unidade}",
                        size=28, weight="bold", color="blue"),
                ft.Divider(color="white10"),
                ft.Row([
                    input_valor,
                    ft.IconButton(ft.Icons.CAMERA_ALT, # Corrigido: Icons
                                  icon_color="blue", on_click=acionar_camera)
                ], alignment="center"),
                texto_consumo,
                ft.Row([
                    ft.FilledButton("SALVAR", icon=ft.Icons.SAVE, # Corrigido: Icons
                                    on_click=salvar_leitura, width=150),
                    ft.IconButton(
                        icon=ft.Icons.SKIP_NEXT, # Corrigido: Icons
                        icon_color="white54",
                        tooltip="Pular esta unidade",
                        on_click=pular_unidade
                    )
                ], alignment="center"),
            ],
            horizontal_alignment="center", spacing=20
        )
    )