import flet as ft


async def inicializar_camera(page: ft.Page, ao_concluir_ocr):
    # ... (seu código de limpeza de overlay aqui) ...

    async def resultado_selecao(e: ft.FilePickerResultEvent):
        if e.files:
            # Sua lógica de pegar o caminho do arquivo e mandar pro OCR
            pass

    # CRIAÇÃO DO OBJETO
    seletor = ft.FilePicker(on_result=resultado_selecao)

    # ADICIONANDO NA PÁGINA
    if seletor not in page.overlay:
        page.overlay.append(seletor)

    await page.update_async()

    # --- A LINHA QUE ESTÁ FALTANDO NO SEU É ESTA: ---
    return seletor
