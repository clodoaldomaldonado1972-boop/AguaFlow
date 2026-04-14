import urllib.parse
import flet as ft

class SuporteHelper:
    """Centraliza a ajuda e documentação do sistema AguaFlow."""
    
    NUMERO_SUPORTE = "5518981337316"
    # Link para o manual (pode ser um link do Google Drive ou GitHub)
    URL_MANUAL = "https://docs.google.com/document/d/16K78tdhAwYScNKrxz4Qnw0g-AXXT-b3gv10UHFzX1SM/edit?usp=sharing"

    @staticmethod
    def abrir_whatsapp_suporte(page: ft.Page, usuario_email: str):
        mensagem = f"Olá! Sou o usuário {usuario_email} e preciso de ajuda com o AguaFlow."
        texto_url = urllib.parse.quote(mensagem)
        page.launch_url(f"https://wa.me/{SuporteHelper.NUMERO_SUPORTE}?text={texto_url}")

    @staticmethod
    def abrir_manual(page: ft.Page):
        page.launch_url(SuporteHelper.URL_MANUAL)