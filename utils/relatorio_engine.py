import csv
import os
import smtplib
from email.message import EmailMessage
from fpdf import FPDF
from datetime import datetime

class RelatorioEngine:
    """Motor de processamento de documentos e comunicações do AguaFlow."""

    @staticmethod
    def gerar_relatorio_consumo(dados):
        """Gera um PDF formatado com as leituras do mês."""
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            
            # Cabeçalho
            pdf.cell(200, 10, txt="AguaFlow - Relatório de Consumo Mensal", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"Condomínio Vivere Prudente - Data: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='C')
            pdf.ln(10)

            # Tabela de Dados
            pdf.set_font("Arial", "B", 10)
            pdf.cell(40, 10, "Unidade", 1)
            pdf.cell(60, 10, "Data Leitura", 1)
            pdf.cell(40, 10, "Valor (m³)", 1)
            pdf.cell(50, 10, "Status", 1)
            pdf.ln()

            pdf.set_font("Arial", size=10)
            for item in dados:
                pdf.cell(40, 10, str(item.get("unidade", "N/A")), 1)
                pdf.cell(60, 10, str(item.get("data_leitura", "N/A")), 1)
                pdf.cell(40, 10, str(item.get("valor", "0")), 1)
                pdf.cell(50, 10, "Sincronizado", 1)
                pdf.ln()

            caminho_pdf = "relatorio_consumo.pdf"
            pdf.output(caminho_pdf)
            return os.path.abspath(caminho_pdf)
        except Exception as e:
            raise Exception(f"Erro ao gerar PDF: {str(e)}")

    @staticmethod
    def gerar_csv_consumo(dados):
        """Gera um arquivo CSV para integração com planilhas (Excel)."""
        try:
            caminho_csv = "dados_consumo.csv"
            campos = ["unidade", "valor", "data_leitura"]
            
            with open(caminho_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=campos)
                writer.writeheader()
                for item in dados:
                    # Filtra apenas os campos necessários para o CSV
                    writer.writerow({k: item[k] for k in campos if k in item})
            
            return os.path.abspath(caminho_csv)
        except Exception as e:
            raise Exception(f"Erro ao gerar CSV: {str(e)}")

    @staticmethod
    def enviar_relatorios_por_email(pdf_path, csv_path, destinatario="escritorio@vivereprudente.com.br"):
        """Envia os arquivos gerados via SMTP (E-mail)."""
        # --- CONFIGURAÇÕES DO SERVIDOR (AJUSTAR COM SEU E-MAIL) ---
        EMAIL_ORIGEM = "seu_email@gmail.com"
        SENHA_APP = "sua_senha_app_google" 
        
        try:
            msg = EmailMessage()
            msg['Subject'] = f"Relatório de Consumo Água/Gás - {datetime.now().strftime('%m/%Y')}"
            msg['From'] = EMAIL_ORIGEM
            msg['To'] = destinatario
            msg.set_content(f"Prezados,\n\nSegue em anexo o relatório de fechamento de leituras do Condomínio Vivere Prudente.\n\nGerado automaticamente pelo AguaFlow.")

            # Anexar PDF
            with open(pdf_path, 'rb') as f:
                msg.add_attachment(f.read(), maintype='application', subtype='pdf', filename=os.path.basename(pdf_path))

            # Anexar CSV
            with open(csv_path, 'rb') as f:
                msg.add_attachment(f.read(), maintype='text', subtype='csv', filename=os.path.basename(csv_path))

            # Envio via Gmail (exemplo)
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(EMAIL_ORIGEM, SENHA_APP)
                smtp.send_message(msg)
            
            return True, "Relatórios enviados com sucesso para o escritório!"
        except Exception as e:
            return False, f"Falha no envio do e-mail: {str(e)}"