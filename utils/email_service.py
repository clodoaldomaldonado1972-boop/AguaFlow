import smtplib
import os
import glob
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from datetime import datetime
from dotenv import load_dotenv

# Carrega as configurações do arquivo .env
load_dotenv()

def enviar_relatorios_por_email(lista_caminhos_arquivos):
    """
    Envia os relatórios gerados e realiza a limpeza de ficheiros temporários.
    """
    email_remetente = os.getenv("EMAIL_USER")
    senha_app = os.getenv("EMAIL_PASS")
    email_destinatario = os.getenv("EMAIL_DESTINATARIO", "clodoaldo.maldonado1972@gmail.com")

    if not email_remetente or not senha_app:
        print("❌ Erro: Credenciais de e-mail não configuradas no .env")
        return False

    # 1. CONFIGURAÇÃO DA MENSAGEM
    msg = MIMEMultipart()
    msg['From'] = email_remetente
    msg['To'] = email_destinatario
    msg['Subject'] = f"Relatórios AguaFlow - Vivere Prudente - {datetime.now().strftime('%d/%m/%Y')}"

    corpo = f"""
    Olá,
    
    Seguem em anexo os relatórios de medição do Condomínio Vivere Prudente.
    Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}
    
    Este é um envio automático do sistema AguaFlow.
    """
    msg.attach(MIMEText(corpo, 'plain'))

    # 2. ANEXAR FICHEIROS
    arquivos_anexados = 0
    try:
        for caminho in lista_caminhos_arquivos:
            if os.path.exists(caminho):
                with open(caminho, "rb") as anexo:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(anexo.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition", 
                        f"attachment; filename={os.path.basename(caminho)}"
                    )
                    msg.attach(part)
                    arquivos_anexados += 1

        if arquivos_anexados == 0:
            print("❌ Erro: Nenhum ficheiro para anexar.")
            return False

        # 3. ENVIO SEGURO
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(email_remetente, senha_app)
            server.send_message(msg)
            
        print(f"✅ E-mail enviado com sucesso!")

        # 4. LÓGICA DE MANUTENÇÃO (Absorvida do mailer.py)
        # Limpa a pasta de relatórios para economizar espaço no Android
        pasta_relatorios = "relatorios"
        if os.path.exists(pasta_relatorios):
            # Remove PDFs enviados e CSVs temporários
            temporarios = glob.glob(os.path.join(pasta_relatorios, "*.*"))
            for f in temporarios:
                try:
                    os.remove(f)
                    print(f"🗑️ Limpeza: {os.path.basename(f)} removido.")
                except:
                    pass

        return True

    except Exception as e:
        print(f"❌ Erro no serviço de e-mail: {e}")
        return False