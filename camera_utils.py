import flet as ft
import os
import leitor_ocr


async def inicializar_camera(page: ft.Page, ao_concluir_ocr):
    page.overlay.clear()
    page.update()

    async def resultado_selecao(e: ft.FilePickerResultEvent):
        if e.files and e.files[0].path:
            caminho_foto = e.files[0].path
            print(f"📷 Foto capturada em: {caminho_foto}")

            # Processamento OCR
            valor_detectado = leitor_ocr.processar_leitura_imagem(caminho_foto)

            if not valor_detectado:
                print("⚠️ OCR não detectou números.")

            # AQUI ESTAVA O ERRO: Mudamos de 'await' para 'run_task'
            # Isso evita que o Flet tente dar await em algo que retorna None.
            page.run_task(ao_concluir_ocr, None, valor_detectado)
        else:
            print("🚫 Seleção cancelada.")

    seletor = ft.FilePicker(on_result=resultado_selecao)

    if seletor not in page.overlay:
        page.overlay.append(seletor)

    page.update()
    return seletor
