import flet as ft
import processamento


async def inicializar_camera(page: ft.Page, ao_concluir_ocr):
    # Remova aquele 'a' que estava aqui em cima!

    # Limpeza de controles antigos
    for control in page.overlay[:]:
        if isinstance(control, ft.FilePicker):
            page.overlay.remove(control)

    async def resultado_selecao(e: ft.FilePickerResultEvent):
        if e.files:
            caminho = e.files[0].path
            id_qr, valor_ocr = processamento.processar_foto_hidrometro(caminho)
            ao_concluir_ocr(id_qr, valor_ocr)

        # Lembre-se: apenas page.update()
        page.update()

    seletor = ft.FilePicker()
    seletor.on_result = resultado_selecao

    page.overlay.append(seletor)
    page.update()

    return seletor
