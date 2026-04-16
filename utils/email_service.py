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
    # IMPORTANTE: Aqui deve estar a "Senha de App" de 16 dígitos do Google
    senha_app = os.getenv("EMAIL_PASS")
    email_destinatario = os.getenv("EMAIL_DESTINATARIO", "clodoaldomaldonado112@gmail.com")

    # Verifica se as credenciais existem
    if not email_remetente or not senha_app:
        print("❌ Erro: Credenciais de e-mail não encontradas no .env")
        return False

    # Verifica se o arquivo PDF realmente existe antes de tentar abrir
    if not os.path.exists(caminho_pdf):
        print(f"❌ Erro: Arquivo {caminho_pdf} não encontrado.")
        return False

    msg = MIMEMultipart()
    msg['From'] = email_remetente
    msg['To'] = email_destinatario
    msg['Subject'] = f"Relatório AguaFlow - Vivere Prudente - {datetime.now().strftime('%d/%m/%Y')}"

    try:
        # Anexando o arquivo PDF de forma segura
        with open(caminho_pdf, "rb") as anexo:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(anexo.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition", f"attachment; filename={os.path.basename(caminho_pdf)}")
            msg.attach(part)

        # Configuração para Gmail usando SSL (Porta 465)
        # Mais seguro e estável para envios automatizados
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(email_remetente, senha_app)
            server.send_message(msg)
            
        print(f"✅ Relatório enviado com sucesso para {email_destinatario}!")
        return True

    except smtplib.SMTPAuthenticationError:
        print("❌ Erro 535: Falha na autenticação. Verifique se a 'Senha de App' está correta.")
        return False
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {str(e)}")
        return False