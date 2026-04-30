import flet as ft
import asyncio
import cv2
import numpy as np
from . import leitor_ocr


class CameraUtils:
    """Utilitários para captura e processamento de imagens via câmera/scanner."""

    @staticmethod
    async def inicializar_camera(page: ft.Page, ao_concluir_ocr):
        """Inicializa seletor de arquivos para captura de imagem."""
        def resultado_selecao(e: ft.FilePickerResultEvent):
            if e.files and e.files[0].path:
                caminho_foto = e.files[0].path

                async def processar():
                    resultado = await CameraUtils.processar_imagem_ocr(caminho_foto)
                    ao_concluir_ocr(resultado)

                page.run_task(processar)

        seletor = CameraUtils._obter_file_picker(page)
        seletor.on_result = resultado_selecao

        if seletor not in page.overlay:
            page.overlay.append(seletor)

        page.update()
        await asyncio.sleep(0.5)
        await seletor.pick_files()

    @staticmethod
    def _obter_file_picker(page: ft.Page) -> ft.FilePicker:
        """Retorna FilePicker existente ou cria nova."""
        for control in page.overlay:
            if isinstance(control, ft.FilePicker):
                return control

        seletor = ft.FilePicker()
        page.overlay.append(seletor)
        return seletor

    @staticmethod
    async def processar_imagem_ocr(caminho_imagem: str):
        """Processa imagem e extrai leitura via OCR."""
        img_array = np.fromfile(caminho_imagem, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is not None:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            img_preprocessada = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
        else:
            img_preprocessada = None

        return await asyncio.to_thread(leitor_ocr.processar_leitura_completa, img_preprocessada)

    @staticmethod
    def aplicar_filtro_ruido(img: np.ndarray) -> np.ndarray:
        """Aplica filtro de ruído Gaussiano."""
        if img is None:
            return None
        return cv2.GaussianBlur(img, (5, 5), 0)

    @staticmethod
    def realce_bordas(img: np.ndarray) -> np.ndarray:
        """Realça bordas para melhor detecção de dígitos."""
        if img is None:
            return None
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    @staticmethod
    def corrigir_inclinacao(img: np.ndarray) -> np.ndarray:
        """Corrige inclinação da imagem para melhor OCR."""
        if img is None:
            return None

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        coords = np.column_stack(np.where(gray > 0))
        angle = cv2.minAreaRect(coords)[-1]

        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        (h, w) = img.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)