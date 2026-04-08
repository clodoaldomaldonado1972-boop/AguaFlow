import flet as ft


class PreferenciasLeitura:
    @staticmethod
    def get_modo_ocr(page: ft.Page):
        """Retorna True para Câmera (OCR) ou False para Manual."""
        # Busca no armazenamento local do dispositivo
        valor = page.client_storage.get("ocr_automatico")
        # Se for a primeira vez, o padrão será True (Câmera)
        return valor if valor is not None else True

    @staticmethod
    def set_modo_ocr(page: ft.Page, valor: bool):
        """Salva a escolha do utilizador no dispositivo."""
        page.client_storage.set("ocr_automatico", valor)
        page.update()
