import flet as ft
import asyncio
import cv2
import numpy as np
from . import leitor_ocr  # Import relativo para funcionar dentro do pacote views


async def inicializar_camera(page: ft.Page, ao_concluir_ocr):
    def resultado_selecao(e: ft.FilePickerResultEvent):
        if e.files and e.files[0].path:
            caminho_foto = e.files[0].path

            async def processar():
                # Carregar a imagem
                img_array = np.fromfile(caminho_foto, np.uint8)
                img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

                if img is not None:
                    # Pré-processamento: converter para escala de cinza
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                    # Aplicar CLAHE para realce de contraste
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                    enhanced = clahe.apply(gray)

                    # Usar a imagem pré-processada
                    img_preprocessada = cv2.cvtColor(
                        enhanced, cv2.COLOR_GRAY2BGR)
                else:
                    img_preprocessada = None

                # Processar a imagem com OCR
                resultado = await asyncio.to_thread(leitor_ocr.processar_leitura_completa, img_preprocessada)
                # Retorna o dicionário completo para a interface
                ao_concluir_ocr(resultado)

            page.run_task(processar)

    # Verificar se já existe um FilePicker no overlay
    seletor_existente = None
    for control in page.overlay:
        if isinstance(control, ft.FilePicker):
            seletor_existente = control
            break

    if seletor_existente:
        seletor = seletor_existente
    else:
        # Flet 0.84.0 compatibility: define on_result after object creation
        seletor = ft.FilePicker()
        seletor.on_result = resultado_selecao
        page.overlay.append(seletor)

    # Atualizar a página para registrar o componente
    page.update()

    # Pequeno delay para dar tempo ao Flet registrar no Windows
    await asyncio.sleep(1.0)

    # Agora chamar o seletor de arquivos
    await seletor.pick_files()