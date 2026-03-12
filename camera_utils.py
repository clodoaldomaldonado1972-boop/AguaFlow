import flet as ft
import processamento  # Módulo de OCR/Inteligência
import asyncio


async def inicializar_camera(page: ft.Page, ao_concluir_ocr):
    """
    Prepara o componente invisível FilePicker e o injeta na página.
    """
    # 1. Limpeza: Remove seletores antigos para não ocupar memória
    for control in page.overlay[:]:
        if isinstance(control, ft.FilePicker):
            page.overlay.remove(control)

    # 2. Lógica de resposta: O que acontece após o usuário tirar a foto
    async def resultado_selecao(e: ft.FilePickerResultEvent):
        if e.files:
            caminho = e.files[0].path

            # Feedback visual: Barra de progresso para o usuário esperar o OCR
            page.splash = ft.ProgressBar()
            page.update()

            try:
                # Executa o OCR em segundo plano para não travar a interface (Thread secundária)
                loop = asyncio.get_event_loop()
                id_qr, valor_ocr = await loop.run_in_executor(
                    None, processamento.processar_foto_hidrometro, caminho
                )

                # Devolve os dados extraídos para a tela de medição via 'callback'
                await ao_concluir_ocr(id_qr, valor_ocr)
            except Exception as ex:
                print(f"Erro no processamento: {ex}")
            finally:
                page.splash = None  # Remove a barra de progresso após terminar
                page.update()

    # 3. Criação do controle e vínculo obrigatório com a página
    seletor = ft.FilePicker(on_result=resultado_selecao)
    page.overlay.append(seletor)

    # IMPORTANTE: Força o seletor a saber a qual página ele pertence
    seletor.page = page
    await page.update_async()

    return seletor
