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

# Configuração de logs para rastrearmos o que acontece no envio
logger = logging.getLogger("AguaFlow_Email")

# Carrega as configurações do arquivo .env (EMAIL_USER, EMAIL_PASS, etc)
load_dotenv()

def enviar_relatorios_por_email(lista_caminhos_arquivos):
    """
    Envia os relatórios gerados (PDF/CSV) por e-mail e realiza a limpeza automática.
    """
    email_remetente = os.getenv("EMAIL_USER")
    senha_app = os.getenv("EMAIL_PASS")
    # E-mail de destino padrão caso não esteja no .env
    email_destinatario = os.getenv("EMAIL_DESTINATARIO", "clodoaldo.maldonado1972@gmail.com")

    # Validação inicial de segurança
    if not email_remetente or not senha_app:
        logger.error("❌ Credenciais de e-mail não configuradas no .env")
        return False

    # 1. MONTAGEM DA MENSAGEM
    msg = MIMEMultipart()
    msg['From'] = email_remetente
    msg['To'] = email_destinatario
    msg['Subject'] = f"Relatórios AguaFlow - Vivere Prudente - {datetime.now().strftime('%d/%m/%Y')}"

    corpo_email = f"""
    Olá,
    
    Seguem em anexo os relatórios de medição (Consumo de Água e Gás) do Condomínio Vivere Prudente.
    
    Os arquivos incluem:
    - Relatório em PDF (Visualização e Impressão)
    - Relatório em CSV (Dados para Excel)
    
    Este é um envio automático do sistema AguaFlow.
    Data do envio: {datetime.now().strftime('%d/%m/%Y às %H:%M')}
    """
    msg.attach(MIMEText(corpo_email, 'plain'))

    # 2. ANEXO DOS ARQUIVOS (DINÂMICO)
    arquivos_anexados = 0
    for caminho in lista_caminhos_arquivos:
        if caminho and os.path.exists(caminho):
            try:
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
                    logger.info(f"📎 Arquivo anexado: {os.path.basename(caminho)}")
            except Exception as e:
                logger.error(f"⚠️ Erro ao anexar {caminho}: {e}")

    if arquivos_anexados == 0:
        logger.warning("❌ Nenhum arquivo válido foi encontrado para anexar.")
        return False

    # 3. CONEXÃO E ENVIO SEGURO (SSL)
    try:
        # Usamos o porto 465 (SSL) por ser o padrão mais seguro para Gmail
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(email_remetente, senha_app)
            server.send_message(msg)
            
        logger.info(f"✅ E-mail enviado com sucesso para {email_destinatario}!")
        
        # 4. LIMPEZA DE MANUTENÇÃO
        # Após o envio, limpamos os arquivos para não ocupar espaço desnecessário
        limpar_pasta_relatorios()
        return True

    except Exception as e:
        logger.error(f"❌ Falha crítica no envio: {e}")
        return False

def limpar_pasta_relatorios():
    """
    Remove todos os arquivos da pasta 'relatorios' após o envio bem-sucedido.
    """
    pasta = "relatorios"
    if os.path.exists(pasta):
        # Busca por qualquer extensão (pdf, csv, etc)
        arquivos = glob.glob(os.path.join(pasta, "*.*"))
        for f in arquivos:
            try:
                os.remove(f)
                logger.info(f"🗑️ Limpeza: {os.path.basename(f)} removido.")
            except Exception as e:
                logger.error(f"Não foi possível remover {f}: {e}")