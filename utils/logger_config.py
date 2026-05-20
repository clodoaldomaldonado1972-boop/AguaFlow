import logging
import os
import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from logging.handlers import RotatingFileHandler
from datetime import datetime
from dotenv import load_dotenv

try:
    from utils.updater import VERSION
except ImportError:
    VERSION = "v?.?.?"

load_dotenv()

# Caminho resolvido uma vez no boot — reutilizado pelo dashboard_saude
_LOG_FILE_PATH: str = ""


def get_log_path() -> str:
    """Retorna o caminho do arquivo de log, compatível com desktop e Android."""
    return _LOG_FILE_PATH


def setup_logging():
    """
    Configura o sistema de log com rotação automática.
    - Android: grava em FLET_APP_STORAGE_DATA (sandbox do app, com permissão de escrita)
    - Desktop: grava na raiz do projeto
    - RotatingFileHandler: máx 1 MB por arquivo, 3 backups → nunca passa de ~4 MB
    - Nível INFO em produção; DEBUG só via variável de ambiente AGUAFLOW_DEBUG=1
    """
    global _LOG_FILE_PATH

    # Resolve o diretório correto conforme plataforma
    app_storage = os.environ.get("FLET_APP_STORAGE_DATA", "")
    if app_storage:
        log_dir = app_storage                                    # Android sandbox
    else:
        log_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Desktop

    _LOG_FILE_PATH = os.path.join(log_dir, "aguaflow.log")

    level = logging.DEBUG if os.environ.get("AGUAFLOW_DEBUG") == "1" else logging.INFO

    # RotatingFileHandler: 1 MB por arquivo, 3 backups (máx ~4 MB no dispositivo)
    try:
        file_handler = RotatingFileHandler(
            _LOG_FILE_PATH,
            maxBytes=1 * 1024 * 1024,   # 1 MB
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%d/%m %H:%M:%S",
        ))
    except Exception:
        file_handler = None  # Sem permissão de escrita — continua sem arquivo

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(level)
    stream_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%d/%m %H:%M:%S",
    ))

    handlers = [stream_handler]
    if file_handler:
        handlers.append(file_handler)

    logging.basicConfig(level=level, handlers=handlers, force=True)

    # Silencia ruído sem valor diagnóstico
    for noisy in ("hpack", "httpcore", "httpx", "PIL.TiffImagePlugin", "PIL", "flet_transport"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger(__name__).info(
        f"Log iniciado — arquivo: {_LOG_FILE_PATH} | nível: {logging.getLevelName(level)}"
    )


def enviar_report_erro(mensagem_erro: str, unidade: str = "N/A", leiturista: str = "N/A"):
    """Envia alerta de erro por e-mail em thread daemon (não bloqueia a UI)."""
    def _enviar():
        EMAIL_USER   = os.getenv("EMAIL_USER")
        EMAIL_PASS   = os.getenv("EMAIL_PASS")
        EMAIL_DESTINO = os.getenv("EMAIL_DESTINO", "seu-email@gmail.com")

        if not all([EMAIL_USER, EMAIL_PASS]):
            logging.warning("SMTP: credenciais ausentes no .env")
            return
        try:
            msg = MIMEMultipart()
            msg["From"]    = EMAIL_USER
            msg["To"]      = EMAIL_DESTINO
            msg["Subject"] = f"ALERTA ERRO: AguaFlow {VERSION} - Vivere Prudente"
            corpo = (
                f"ERRO CRITICO DETECTADO\n"
                f"Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
                f"Versao: {VERSION}\n"
                f"Leiturista: {leiturista}\n"
                f"Unidade: {unidade}\n\n"
                f"{mensagem_erro}"
            )
            msg.attach(MIMEText(corpo, "plain"))
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
                server.starttls()
                server.login(EMAIL_USER, EMAIL_PASS)
                server.send_message(msg)
            logging.info("Report de erro enviado por e-mail.")
        except Exception as e:
            logging.error(f"Falha ao enviar report de e-mail: {e}")

    threading.Thread(target=_enviar, daemon=True).start()


def testar_configuracao_email():
    """Verificação silenciosa de autenticação SMTP no boot do app."""
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")
    if not EMAIL_USER or not EMAIL_PASS:
        return
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
        logging.info("SMTP: autenticado com sucesso.")
    except Exception as e:
        logging.error(f"SMTP: falha na autenticacao inicial: {e}")
