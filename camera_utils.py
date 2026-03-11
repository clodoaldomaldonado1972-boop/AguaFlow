import flet as ft
import processamento


def inicializar_camera(page, ao_concluir_ocr):
    """
    Configura o FilePicker de forma isolada e gerencia o overlay da página.
    """
    # Limpeza para evitar conflito de múltiplos FilePickers (Erro 'Unknown Control')
    for control in page.overlay[:]:
        if isinstance(control, ft.FilePicker):
            page.overlay.remove(control)

    def resultado_selecao(e: ft.FilePickerResultEvent):
        if e.files:
            caminho_foto = e.files[0].path
            # Chama o processamento (OCR/QR Code) definido no AguaFlow
            id_qr, valor_ocr = processamento.processar_foto_hidrometro(
                caminho_foto)
            # Devolve os dados para a função de retorno na tela principal
            ao_concluir_ocr(id_qr, valor_ocr)
        page.update()

    # Cria o seletor compatível com versões que não aceitam on_result no construtor
    seletor = ft.FilePicker()
    seletor.on_result = resultado_selecao

    page.overlay.append(seletor)
    page.update()  # Garante que o celular 'veja' o seletor antes do clique

    return seletor
