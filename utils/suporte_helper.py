import urllib.parse
import flet as ft

class SuporteHelper:
    """
    Classe utilitária que centraliza o suporte e documentação do sistema AguaFlow.
    Gere a abertura de URLs externas como WhatsApp e Manuais no Google Docs.
    """
    
    # Configurações de destino do suporte
    NUMERO_SUPORTE = "5518981337316" # Seu número configurado
    URL_MANUAL = "https://docs.google.com/document/d/16K78tdhAwYScNKrxz4Qnw0g-AXXT-b3gv10UHFzX1SM/edit?usp=sharing"

    @staticmethod
    def abrir_whatsapp_suporte(page: ft.Page, usuario_email: str):
        """
        Abre o WhatsApp com uma mensagem pré-definida contendo o e-mail do operador.
        IHC: Facilita a identificação do problema pelo administrador.
        """
        mensagem = f"Olá! Sou o utilizador {usuario_email} e preciso de ajuda técnica com o AguaFlow."
        # Codifica o texto para formato de URL (converte espaços em %20, etc.)
        texto_url = urllib.parse.quote(mensagem)
        
        # Lança a URL no navegador padrão ou aplicação de WhatsApp do telemóvel
        page.launch_url(f"https://wa.me/{SuporteHelper.NUMERO_SUPORTE}?text={texto_url}")

    @staticmethod
    def abrir_manual(page: ft.Page):
        """
        Abre o manual técnico completo hospedado na nuvem.
        Método padronizado para ser chamado pela Ajuda e Configurações.
        """
        try:
            page.launch_url(SuporteHelper.URL_MANUAL)
        except Exception as e:
            print(f"Erro ao abrir manual: {e}")

    @staticmethod
    def abrir_manual_externo(page: ft.Page):
        """Alias para manter compatibilidade com versões anteriores do código."""
        SuporteHelper.abrir_manual(page)