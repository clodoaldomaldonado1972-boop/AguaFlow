import flet as ft
import os
import leitor_ocr  # Importando o seu módulo de leitura


async def inicializar_camera(page: ft.Page, ao_concluir_ocr):
    # Limpeza preventiva para não acumular seletores na memória do celular
    page.overlay.clear()
    page.update()

    async def resultado_selecao(e: ft.FilePickerResultEvent):
        if e.files and e.files[0].path:
            caminho_foto = e.files[0].path
            print(f"📷 Foto capturada em: {caminho_foto}")

            # --- A MÁGICA ACONTECE AQUI ---
            # Chamamos a função do seu arquivo leitor_ocr.py passando a foto
            valor_detectado = leitor_ocr.processar_leitura_imagem(caminho_foto)

            # Se o OCR falhar e retornar vazio, podemos tratar aqui ou deixar
            # o usuário digitar manualmente na tela de medição.
            if not valor_detectado:
                print(
                    "⚠️ OCR não conseguiu ler os números. Aguardando digitação manual.")

            # Chama o callback que definimos lá no medicao.py para preencher o campo
            await ao_concluir_ocr(None, valor_detectado)
        else:
            print("🚫 Seleção cancelada pelo usuário.")

    # Criação do objeto FilePicker
    seletor = ft.FilePicker(on_result=resultado_selecao)

    # Adicionando na página (overlay)
    if seletor not in page.overlay:
        page.overlay.append(seletor)

    # Atualiza a página para registrar o seletor
    page.update()

    return seletor
