import flet as ft
import leitor_ocr


async def inicializar_camera(page: ft.Page, ao_concluir_ocr):

    def resultado_selecao(e: ft.FilePickerResultEvent):
        if e.files and e.files[0].path:
            caminho_foto = e.files[0].path
            print(f"📷 Foto recebida: {caminho_foto}")

            def processar():
                valor_detectado = leitor_ocr.processar_leitura_imagem(
                    caminho_foto)
                page.run_task(ao_concluir_ocr, None, valor_detectado)

            page.run_task(processar)
        else:
            print("🚫 Seleção cancelada.")

    # Criamos o seletor sem restrições que bloqueiam a câmera no Android
    seletor = ft.FilePicker(on_result=resultado_selecao)

    if seletor not in page.overlay:
        page.overlay.append(seletor)

    page.update()
    return seletor
