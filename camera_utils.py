import flet as ft
import processamento


def inicializar_camera(page, ao_concluir_ocr):
    # Limpeza profunda para evitar o erro de "Unknown Control" no Samsung M14
    for control in page.overlay[:]:
        if isinstance(control, ft.FilePicker):
            page.overlay.remove(control)

    def resultado_selecao(e: ft.FilePickerResultEvent):
        if e.files:
            caminho = e.files[0].path
            # Chama o módulo de visão computacional
            id_qr, valor_ocr = processamento.processar_foto_hidrometro(caminho)
            ao_concluir_ocr(id_qr, valor_ocr)
        page.update()

    # Criando o seletor de forma resiliente
    seletor = ft.FilePicker()
    seletor.on_result = resultado_selecao

    page.overlay.append(seletor)
    page.update()  # IMPORTANTE: Sincroniza o componente com o celular
    return seletor
