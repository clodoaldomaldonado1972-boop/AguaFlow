import flet as ft
import processamento
import asyncio


async def inicializar_camera(page: ft.Page, ao_concluir_ocr):
    """
    Inicializa o seletor de arquivos e gerencia a lógica de OCR.
    """
    # 1. Limpeza profunda de overlays antigos para evitar conflitos de ID
    for control in page.overlay[:]:
        if isinstance(control, ft.FilePicker):
            page.overlay.remove(control)

    async def resultado_selecao(e: ft.FilePickerResultEvent):
        if e.files:
            caminho = e.files[0].path

            # 2. Chamada da lógica de OCR (Espera o processamento sem travar a UI)
            # Como processamento pode ser pesado, rodamos em uma thread ou usamos await se disponível
            try:
                # Se o seu processamento for síncrono, o ideal é não travar o loop
                id_qr, valor_ocr = processamento.processar_foto_hidrometro(
                    caminho)

                # 3. Retorna o resultado para a função de callback da medicao.py
                # Usamos page.run_task para garantir que a atualização da UI seja segura
                await ao_concluir_ocr(id_qr, valor_ocr)

            except Exception as ex:
                print(f"Erro no processamento de imagem: {ex}")

        page.update()

    # 4. Criação do seletor único para esta instância da tela
    seletor = ft.FilePicker(on_result=resultado_selecao)
    page.overlay.append(seletor)
    page.update()

    return seletor
