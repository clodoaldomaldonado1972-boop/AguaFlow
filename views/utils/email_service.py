import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from dotenv import load_dotenv

# Carrega as configurações do arquivo .env
load_dotenv()

def enviar_relatorio_por_email(caminho_pdf):
    # Puxa os dados do seu arquivo .env
    email_remetente = os.getenv("EMAIL_USER")
    senha_app = os.getenv("EMAIL_PASS")
    email_destinatario = os.getenv("EMAIL_DESTINATARIO")

    if not email_remetente or not senha_app:
        print("❌ Erro: Credenciais de e-mail não encontradas no .env")
        return False

    msg = MIMEMultipart()
    msg['From'] = email_remetente
    msg['To'] = email_destinatario
    msg['Subject'] = f"Relatório AguaFlow - Vivere Prudente - {datetime.now().strftime('%d/%m/%Y')}"

    try:
        with open(caminho_pdf, "rb") as anexo:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(anexo.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename={os.path.basename(caminho_pdf)}")
            msg.attach(part)

        # Configuração para Gmail
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(email_remetente, senha_app)
        server.send_message(msg)
        server.quit()
        
        print(f"📧 E-mail enviado com sucesso para {email_destinatario}!")
        return True
    except Exception as e:
        print(f"❌ Falha ao enviar e-mail: {str(e)}")
        return False
    