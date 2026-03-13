import flet as ft
import os


async def inicializar_camera(page: ft.Page, ao_concluir_ocr):
    # Limpeza preventiva para não acumular seletores na memória do celular
    page.overlay.clear()
    page.update()

    async def resultado_selecao(e: ft.FilePickerResultEvent):
        if e.files and e.files[0].path:
            caminho_foto = e.files[0].path
            print(f"📷 Foto capturada em: {caminho_foto}")

            # Aqui simulamos o OCR ou chamamos sua função de processamento
            # Por enquanto, vamos devolver um valor fixo ou processar o ID
            valor_detectado = 123.45  # Exemplo de leitura detectada

            # Chama o callback que definimos lá no medicao.py
            await ao_concluir_ocr(None, valor_detectado)
        else:
            print("🚫 Seleção cancelada pelo usuário.")

    # Criação do objeto FilePicker
    seletor = ft.FilePicker(on_result=resultado_selecao)

    # Adicionando na página (overlay é a camada "invisível" para diálogos e arquivos)
    if seletor not in page.overlay:
        page.overlay.append(seletor)

    # Atualiza a página para o Flet registrar o novo seletor
    page.update()

    # A LINHA MÁGICA: Devolve o objeto para quem chamou
    return seletor
