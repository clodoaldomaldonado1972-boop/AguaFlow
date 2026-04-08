import smtplib
import os
import glob
from email.message import EmailMessage
from dotenv import load_dotenv

# Carrega as credenciais do .env localizado na raiz[cite: 17, 19]
load_dotenv()


def enviar_relatorio_email(caminho_pdf, destinatario=None):
    """
    Envia o relatório PDF por e-mail e limpa arquivos CSV temporários da pasta.
    """
    meu_email = os.getenv("EMAIL_USER")
    minha_senha = os.getenv("EMAIL_PASS")

    # Se não for passado um destinatário, usa o e-mail padrão do administrador[cite: 19, 20]
    alvo = destinatario if destinatario else "clodoaldomaldonado112@gmail.com"

    msg = EmailMessage()
    msg['Subject'] = "Relatório de Consumo - Vivere Prudente"
    msg['From'] = meu_email
    msg['To'] = alvo
    msg.set_content(
        f"Olá,\n\nSegue em anexo o relatório de medição.\nArquivo: {os.path.basename(caminho_pdf)}")

    try:
        # 1. Anexa o documento PDF gerado pelo Exportador[cite: 14, 20]
        with open(caminho_pdf, 'rb') as f:
            msg.add_attachment(
                f.read(),
                maintype='application',
                subtype='pdf',
                filename=os.path.basename(caminho_pdf)
            )

        # 2. Conexão segura com o servidor do Gmail
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(meu_email, minha_senha)
            smtp.send_message(msg)

        # --- LÓGICA DE MANUTENÇÃO (LIMPEZA) ---
        # Após o envio, removemos arquivos CSV antigos da pasta 'relatorios'[cite: 1, 20]
        pasta_relatorios = "relatorios"
        if os.path.exists(pasta_relatorios):
            arquivos_csv = glob.glob(os.path.join(pasta_relatorios, "*.csv"))
            for f in arquivos_csv:
                try:
                    os.remove(f)
                except:
                    continue

            print(
                f"✅ Envio OK e {len(arquivos_csv)} arquivos temporários removidos.")

        return True

    except Exception as e:
        print(f"❌ Erro no serviço de e-mail: {e}")
        return False
