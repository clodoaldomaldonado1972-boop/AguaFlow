import flet as ft
import database as db
import camera_utils
import asyncio


async def montar_tela(page: ft.Page, voltar_menu):
    # EXPLICAÇÃO: Declaramos as variáveis no escopo da função principal para que
    # as sub-funções possam acessá-las via 'nonlocal'.
    seletor_camera = None
    processando = False

    # Limpeza de overlay garante que seletores antigos não fiquem presos na memória.
    page.overlay.clear()
    await page.update_async()

    # LÓGICA DE NEGÓCIO: Busca a próxima unidade conforme a sequência do condomínio.
    unidade = db.buscar_proximo_pendente()

    if not unidade:
        return ft.Container(
            expand=True, bgcolor="#1A1C1E", alignment=ft.Alignment(0, 0),
            content=ft.Column([
                ft.Icon(ft.icons.CHECK_CIRCLE, color="green", size=80),
                ft.Text("Todas as medições concluídas!",
                        size=24, color="white"),
                ft.ElevatedButton(
                    "Voltar ao Menu",
                    # CORREÇÃO: page.run_task garante que a função rode no loop correto do Flet.
                    on_click=lambda _: page.run_task(voltar_menu)
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    id_db, nome_unidade, leitura_anterior = unidade[0], unidade[1], unidade[2]
    texto_consumo = ft.Text("Consumo: 0.00 m³", size=18,
                            color="blue", weight="bold")

    def calcular_ao_digitar(e):
        """Calcula o consumo em tempo real e alerta para anomalias no Vivere Prudente."""
        try:
            input_valor.error_text = None
            if input_valor.value:
                val_limpo = input_valor.value.replace(",", ".")
                consumo = float(val_limpo) - leitura_anterior
                texto_consumo.value = f"Consumo: {consumo:.2f} m³"
                # Alerta visual para consumo acima de 20m³ ou negativo.
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
        """Persiste os dados no SQLite e avança para a próxima unidade."""
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
        """Callback acionado após o processamento da imagem (OCR)."""
        if valor_ocr:
            input_valor.value = str(valor_ocr)
            calcular_ao_digitar(None)
        await page.update_async()

    # Inicialização preventiva do FilePicker via utilitário de câmera.
    seletor_camera = await camera_utils.inicializar_camera(page, ao_concluir_ocr)

    async def acionar_camera(e):
        """Gerencia o acionamento da câmera com tratamento de erros."""
        nonlocal seletor_camera
        if seletor_camera is None:
            seletor_camera = await camera_utils.inicializar_camera(page, ao_concluir_ocr)

        if seletor_camera is not None:
            try:
                if seletor_camera not in page.overlay:
                    page.overlay.append(seletor_camera)
                seletor_camera.page = page
                await page.update_async()
                await seletor_camera.pick_files(
                    allow_multiple=False,
                    file_type=ft.FilePickerFileType.IMAGE
                )
            except Exception as ex:
                print(f"Erro interno no seletor: {ex}")
        else:
            page.snack_bar = ft.SnackBar(
                ft.Text("Erro: Câmera não inicializada."))
            page.snack_bar.open = True
            page.update()

    # EXPLICAÇÃO: Função interna para tratar o pulo de unidade de forma assíncrona.
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
                    ft.IconButton(ft.icons.CAMERA_ALT,
                                  icon_color="blue", on_click=acionar_camera)
                ], alignment="center"),
                texto_consumo,
                ft.Row([
                    ft.FilledButton("SALVAR", icon=ft.icons.SAVE,
                                    on_click=salvar_leitura, width=150),
                    ft.IconButton(
                        icon=ft.icons.SKIP_NEXT,
                        icon_color="white54",
                        tooltip="Pular esta unidade",
                        # CORREÇÃO: Chamamos a função assíncrona pular_unidade diretamente.
                        on_click=pular_unidade
                    )
                ], alignment="center"),
            ],
            horizontal_alignment="center", spacing=20
        )
    )
