import urllib.parse
import flet as ft
import os
from dotenv import load_dotenv

load_dotenv()

class AlertasEngine:
    """Engine de alertas via WhatsApp para monitoramento e notificações."""

    CONTATO_PADRAO = os.getenv("WHATSAPP_CONTATO", "5518981337316")

    @staticmethod
    def enviar_alerta_mensagem(page: ft.Page, mensagem: str, contato: str = None):
        """Envia alerta via WhatsApp Web com mensagem personalizada."""
        contato = contato or AlertasEngine.CONTATO_PADRAO
        texto_url = urllib.parse.quote(mensagem)

        link = f"https://wa.me/{contato}?text={texto_url}"
        if page:
            page.launch_url(link)
        return True

    @staticmethod
    def alerta_leitura_pendente(page: ft.Page, unidade: str, tipo: str = "Água"):
        """Alerta de leitura pendente para unidade específica."""
        mensagem = f"Alerta AguaFlow: Leitura de {tipo} da unidade {unidad} está pendente."
        return AlertasEngine.enviar_alerta_mensagem(page, mensagem)

    @staticmethod
    def alerta_vazamento(page: ft.Page, unidade: str, leitura: float):
        """Alerta de possível vazamento baseado em leitura anômala."""
        mensagem = f"ALERTA: Unidade {unidad} - Leitura anômala detectada: {leitura}m³. Possível vazamento!"
        return AlertasEngine.enviar_alerta_mensagem(page, mensagem)

    @staticmethod
    def alerta_fechamento_mes(page: ft.Page, total_unidades: int, periodo: str):
        """Alerta de fechamento mensal enviado ao escritório."""
        mensagem = f"Fechamento mensal {periodo}: {total_unidades} unidades lidas. Relatório enviado."
        return AlertasEngine.enviar_alerta_mensagem(page, mensagem)

    @staticmethod
    def alerta_sync_falha(page: ft.Page, erro: str):
        """Alerta de falha na sincronização com Supabase."""
        mensagem = f"ERRO SYNC: Falha ao sincronizar com Supabase: {erro}"
        return AlertasEngine.enviar_alerta_mensagem(page, mensagem)

    @staticmethod
    def alerta_manutencao(page: ft.Page, mensagem: str):
        """Alerta genérico para manutenção do sistema."""
        return AlertasEngine.enviar_alerta_mensagem(page, f"Manutenção AguaFlow: {mensagem}")