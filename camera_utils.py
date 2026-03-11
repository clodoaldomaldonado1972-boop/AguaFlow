import flet as ft
import processamento

# Adicionamos 'async' aqui


async def inicializar_camera(page, ao_concluir_ocr):
    for control in page.overlay[:]:
        if isinstance(control, ft.FilePicker):
            page.overlay.remove(control)

    async def resultado_selecao(e: ft.FilePickerResultEvent):
        if e.files:
            caminho = e.files[0].path
            id_qr, valor_ocr = processamento.processar_foto_hidrometro(caminho)
            ao_concluir_ocr(id_qr, valor_ocr)
        page.update()

    seletor = ft.FilePicker()
    seletor.on_result = resultado_selecao

    page.overlay.append(seletor)
    page.update()
    return seletor
