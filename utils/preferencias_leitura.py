import flet as ft
import asyncio

class PreferenciasLeitura:
    """
    Gere as preferências de utilizador guardadas localmente no dispositivo.
    Controla se o sistema deve abrir a Câmera (OCR) ou o Teclado (Manual).
    """
    
    CHAVE_OCR = "ocr_automatico"

    @staticmethod
    def get_modo_ocr(page: ft.Page):
        """
        Recupera a preferência de OCR de forma síncrona. 
        Retorna True (Câmera) por padrão se não encontrar nada ou se houver erro.
        """
        try:
            # Tenta recuperar do armazenamento local do Flet
            valor = page.client_storage.get(PreferenciasLeitura.CHAVE_OCR)
            
            # Se for None (primeira execução), assume True (Modo IA Ativo)
            return valor if valor is not None else True
        except Exception as e:
            # Em caso de erro de timeout ou storage, retorna o padrão seguro
            print(f"Aviso [Storage]: Não foi possível ler preferências. Usando padrão: True. Erro: {e}")
            return True

    @staticmethod
    def set_modo_ocr(page: ft.Page, valor: bool):
        """
        Guarda a escolha do utilizador (True para Câmera, False para Manual).
        """
        try:
            page.client_storage.set(PreferenciasLeitura.CHAVE_OCR, valor)
            page.update()
            print(f"DEBUG [Storage]: Preferência OCR guardada como: {valor}")
        except Exception as e:
            print(f"Erro ao guardar preferência: {e}")

    @staticmethod
    async def get_modo_ocr_async(page: ft.Page):
        """
        Versão assíncrona recomendada para evitar Timeouts em dispositivos mais lentos.
        """
        try:
            # Aguarda um pequeno instante para garantir que o bridge do Flet está pronto
            await asyncio.sleep(0.1)
            valor = await page.client_storage.get_async(PreferenciasLeitura.CHAVE_OCR)
            return valor if valor is not None else True
        except Exception:
            return True