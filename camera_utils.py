import flet as ft
import processamento


async def inicializar_camera(page: ft.Page, ao_concluir_ocr):
    # 1. Limpeza de controles antigos (Fundamental para o Android)
    for control in page.overlay[:]:
        if isinstance(control, ft.FilePicker):
            page.overlay.remove(control)

    # 2. Resposta à seleção da foto
    a  # No camera_utils.py:

    # Dentro do camera_utils.py

    async def resultado_selecao(e: ft.FilePickerResultEvent):
        if e.files:
            caminho = e.files[0].path
            # Processamento OCR
            id_qr, valor_ocr = processamento.processar_foto_hidrometro(caminho)
            ao_concluir_ocr(id_qr, valor_ocr)

        # CORREÇÃO AQUI: Mude de await page.update_async() para:
        page.update()

    seletor = ft.FilePicker()
    seletor.on_result = resultado_selecao

    page.overlay.append(seletor)

    # CORREÇÃO AQUI: Mude de await page.update_async() para:
    page.update()

    return seletor
