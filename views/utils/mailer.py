import smtplib
import os
import glob
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

def enviar_relatorio_email(caminho_pdf, destinatario="clodoaldomaldonado112@gmail.com"):
    meu_email = os.getenv("EMAIL_USER")
    minha_senha = os.getenv("EMAIL_PASS")

    msg = EmailMessage()
    msg['Subject'] = "Relatório de Consumo - Vivere Prudente"
    msg['From'] = meu_email
    msg['To'] = destinatario
    msg.set_content(f"Segue o relatório em anexo.\nArquivo: {os.path.basename(caminho_pdf)}")

    try:
        # 1. Anexa o PDF
        with open(caminho_pdf, 'rb') as f:
            msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=os.path.basename(caminho_pdf))

        # 2. Envia o E-mail
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(meu_email, minha_senha)
            smtp.send_message(msg)
        
        # --- A FAXINA COMEÇA AQUI ---
        # Se chegou aqui, o e-mail foi enviado. Vamos limpar a pasta 'relatorios'
        pasta_relatorios = os.path.dirname(caminho_pdf)
        
        # Apaga todos os .csv da pasta
        arquivos_csv = glob.glob(os.path.join(pasta_relatorios, "*.csv"))
        for f in arquivos_csv:
            os.remove(f)
            
        print(f"Limpeza concluída: {len(arquivos_csv)} arquivos CSV removidos.")
        return True

    except Exception as e:
        print(f"Erro no envio ou limpeza: {e}")
        return False