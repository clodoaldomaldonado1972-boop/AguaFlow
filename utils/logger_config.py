import logging
import os
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv

# Tenta importar a versão do updater.py
try:
    # Ajuste para o nome da variável que você usa lá
    from utils.updater import VERSION
except ImportError:
    VERSION = "v?.?.?"  # Fallback caso o arquivo não seja encontrado

load_dotenv()


def enviar_report_erro(mensagem_erro, unidade="N/A", leiturista="N/A"):
    """Envia um e-mail de alerta de forma assíncrona (via Thread) para não travar o app."""
    def _processar_envio():
        EMAIL_USER = os.getenv("EMAIL_USER")
        EMAIL_PASS = os.getenv("EMAIL_PASS")
        EMAIL_DESTINO = os.getenv("EMAIL_DESTINO", "seu-email@gmail.com")

        if not all([EMAIL_USER, EMAIL_PASS]):
            logging.warning("⚠️ SMTP: Credenciais ausentes no .env")
            return

        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_USER
            msg['To'] = EMAIL_DESTINO
            # VERSÃO AUTOMÁTICA NO ASSUNTO:
            msg['Subject'] = f'🚨 ALERTA DE ERRO: AguaFlow {VERSION} - Vivere Prudente'

            corpo = (
                f"🚨 ERRO CRÍTICO DETECTADO\n"
                f"-------------------------\n"
                f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                f"📊 Versão do App: {VERSION}\n"  # Adicionado no corpo também
                f"🏢 Local: Condomínio Vivere Prudente\n"
                f"👤 Leiturista: {leiturista}\n"
                f"📍 Contexto (Unidade): {unidade}\n\n"
                f"📝 Stacktrace / Erro Técnico:\n"
                f"{mensagem_erro}"
            )
            msg.attach(MIMEText(corpo, 'plain'))

            with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
                server.starttls()
                server.login(EMAIL_USER, EMAIL_PASS)
                server.send_message(msg)
            logging.info(
                f"📧 Relatório de erro ({VERSION}) enviado por e-mail com sucesso.")
        except Exception as e:
            logging.error(f"❌ Falha ao enviar report de e-mail: {e}")

    threading.Thread(target=_processar_envio, daemon=True).start()


def testar_configuracao_email():
    """Verificação silenciosa de autenticação SMTP no início do app."""
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")
    if not EMAIL_USER or not EMAIL_PASS:
        return
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
        logging.info("✅ SMTP: Serviço de e-mail autenticado corretamente.")
    except Exception as e:
        logging.error(
            f"❌ SMTP: Falha na autenticação inicial (verifique a senha de app): {e}")


def setup_logging():
    """Configura o sistema de log profissional para o AguaFlow."""
    # Define o arquivo de log na raiz do projeto
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_file = os.path.join(base_dir, "aguaflow_debug.log")

    # Configuração global
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()  # Mantém a saída no terminal para conferência
        ]
    )

    # Silencia ruído de transporte HTTP/2 (hpack, httpcore, httpx)
    # Essas libs emitem centenas de linhas DEBUG por requisição sem valor diagnóstico
    for noisy_lib in ("hpack", "httpcore", "httpx"):
        logging.getLogger(noisy_lib).setLevel(logging.WARNING)
