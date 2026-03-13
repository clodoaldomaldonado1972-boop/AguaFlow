import flet as ft
import os
import leitor_ocr


async def inicializar_camera(page: ft.Page, ao_concluir_ocr):
    page.overlay.clear()
    page.update()  # Correto: sem await

    async def resultado_selecao(e: ft.FilePickerResultEvent):
        if e.files and e.files[0].path:
            caminho_foto = e.files[0].path
            print(f"📷 Foto capturada em: {caminho_foto}")

            # Executa o processamento
            valor_detectado = leitor_ocr.processar_leitura_imagem(caminho_foto)

            if not valor_detectado:
                print("⚠️ OCR não detectou números.")

            # CHAVE DO SUCESSO: Como ao_concluir_ocr é uma função 'async' lá no medicao.py,
            # precisamos manter o await aqui para ele atualizar a tela com o valor.
            await ao_concluir_ocr(None, valor_detectado)
        else:
            print("🚫 Seleção cancelada.")

    seletor = ft.FilePicker(on_result=resultado_selecao)

    if seletor not in page.overlay:
        page.overlay.append(seletor)

    page.update()  # Correto: sem await
    return seletor
