import flet as ft
import processamento
import asyncio


async def inicializar_camera(page: ft.Page, ao_concluir_ocr):
    """
    Gerencia o seletor de arquivos e o processamento OCR de forma isolada.
    """
    # Limpeza de segurança
    for control in page.overlay[:]:
        if isinstance(control, ft.FilePicker):
            page.overlay.remove(control)

    async def resultado_selecao(e: ft.FilePickerResultEvent):
        if e.files:
            caminho = e.files[0].path

            # Feedback visual: Barra de progresso no topo
            page.splash = ft.ProgressBar()
            page.update()

            try:
                # Roda o processamento pesado fora da thread principal para não travar a UI
                loop = asyncio.get_event_loop()
                id_qr, valor_ocr = await loop.run_in_executor(
                    None, processamento.processar_foto_hidrometro, caminho
                )

                await ao_concluir_ocr(id_qr, valor_ocr)
            except Exception as ex:
                print(f"Erro no OCR: {ex}")
            finally:
                page.splash = None  # Remove a barra de progresso
                page.update()

    seletor = ft.FilePicker(on_result=resultado_selecao)
    page.overlay.append(seletor)

    # Vinculo forçado para evitar AssertionError
    seletor.page = page
    await page.update_async()

    return seletor
