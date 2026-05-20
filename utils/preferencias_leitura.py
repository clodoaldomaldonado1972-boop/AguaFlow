import flet as ft


class PreferenciasLeitura:
    """
    Gerencia preferências de usuário persistidas via SharedPreferences (Flet 0.82+).
    Controla se o sistema deve abrir Câmera (OCR) ou Teclado (Manual).
    """

    CHAVE_OCR = "ocr_automatico"

    @staticmethod
    def _get_prefs(page: ft.Page):
        """Localiza a instância de SharedPreferences registrada em page.services."""
        for svc in (page.services or []):
            if isinstance(svc, ft.SharedPreferences):
                return svc
        return None

    @staticmethod
    async def get_modo_ocr(page: ft.Page) -> bool:
        """
        Recupera preferência de OCR de forma assíncrona.
        Retorna True (Câmera/IA ativa) por padrão.
        """
        try:
            prefs = PreferenciasLeitura._get_prefs(page)
            if prefs is None:
                return True
            valor = await prefs.get(PreferenciasLeitura.CHAVE_OCR)
            return valor if valor is not None else True
        except Exception:
            return True

    @staticmethod
    async def set_modo_ocr(page: ft.Page, valor: bool) -> None:
        """Persiste a escolha do usuário (True = Câmera, False = Manual)."""
        try:
            prefs = PreferenciasLeitura._get_prefs(page)
            if prefs is None:
                return
            await prefs.set(PreferenciasLeitura.CHAVE_OCR, valor)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Falha ao salvar preferência OCR: {e}")
