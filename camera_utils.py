import flet as ft
import processamento


async def inicializar_camera(page: ft.Page, ao_concluir_ocr):
    # 1. Limpeza de controles antigos (Fundamental para o Android)
    for control in page.overlay[:]:
        if isinstance(control, ft.FilePicker):
            page.overlay.remove(control)

    # 2. Resposta à seleção da foto
    async def resultado_selecao(e: ft.FilePickerResultEvent):
        if e.files:
            caminho = e.files[0].path
            # Processamento de visão computacional
            id_qr, valor_ocr = processamento.processar_foto_hidrometro(caminho)

            # Devolve os dados para o medicao.py
            ao_concluir_ocr(id_qr, valor_ocr)

        # Mudança aqui: await para garantir sincronia no mobile
        await page.update_async()

    # 3. Criação do componente nativo
    seletor = ft.FilePicker()
    seletor.on_result = resultado_selecao

    page.overlay.append(seletor)

    # Mudança aqui: await para o seletor "nascer" na memória do celular
    await page.update_async()

    return seletor
