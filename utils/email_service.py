import smtplib
import os
import glob
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import datetime
from dotenv import load_dotenv

logger = logging.getLogger("AguaFlow_Email")
load_dotenv()


def limpar_pasta_relatorios():
    """Remove arquivos da pasta 'relatorios' para poupar espaço."""
    pasta = "relatorios"
    if os.path.exists(pasta):
        arquivos = glob.glob(os.path.join(pasta, "*.*"))
        for f in arquivos:
            try:
                os.remove(f)
                logger.info(f"🗑️ Limpeza: {os.path.basename(f)} removido.")
            except Exception as e:
                logger.error(f"Não foi possível remover {f}: {e}")


def enviar_relatorios_por_email(lista_caminhos_arquivos):
    email_remetente = os.getenv("EMAIL_USER")
    senha_app = os.getenv("EMAIL_PASS")
    email_destinatario = os.getenv(
        "EMAIL_DESTINATARIO", "clodoaldo.maldonado1972@gmail.com")

    if not email_remetente or not senha_app:
        logger.error("❌ Credenciais de e-mail não configuradas no .env")
        return False

    msg = MIMEMultipart()
    msg['From'] = email_remetente
    msg['To'] = email_destinatario
    msg['Subject'] = f"Relatórios AguaFlow - Vivere Prudente - {datetime.now().strftime('%d/%m/%Y')}"

    corpo = "Seguem em anexo os relatórios de medição do Condomínio Vivere Prudente."
    msg.attach(MIMEText(corpo, 'plain'))

    for caminho in lista_caminhos_arquivos:
        if caminho and os.path.exists(caminho):
            with open(caminho, "rb") as anexo:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(anexo.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition", f"attachment; filename={os.path.basename(caminho)}")
                msg.attach(part)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(email_remetente, senha_app)
            server.send_message(msg)
        logger.info(f"✅ E-mail enviado com sucesso!")
        # Descomente a linha abaixo para apagar os arquivos após o envio[cite: 5]
        # limpar_pasta_relatorios()
        return True
    except Exception as e:
        logger.error(f"❌ Falha crítica no envio: {e}")
        return False
