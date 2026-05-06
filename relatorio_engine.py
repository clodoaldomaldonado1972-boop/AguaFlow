import csv
import os
import smtplib
from email.message import EmailMessage
from fpdf import FPDF
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


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
            pdf.cell(
                200, 10, txt="AguaFlow - Relatório de Consumo Mensal", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            pdf.cell(
                200, 10, txt=f"Condomínio Vivere Prudente - Data: {datetime.now().strftime('%d/%m/%Y')}", ln=True, align='C')
            pdf.ln(10)

            # --- TABELA 1: ÁGUA ---
            pdf.set_font("Arial", "B", 12)
            pdf.set_text_color(13, 71, 161)  # Azul Escuro
            pdf.cell(200, 10, txt="QUADRO DE CONSUMO: ÁGUA", ln=True, align='L')

            pdf.set_font("Arial", "B", 10)
            pdf.set_text_color(0, 0, 0)
            pdf.set_fill_color(200, 220, 255)  # Fundo Azul Claro
            pdf.cell(40, 10, "Unidade", 1, 0, 'C', True)
            pdf.cell(90, 10, "Data/Hora Coleta", 1, 0, 'C', True)
            pdf.cell(60, 10, "Leitura (m3)", 1, 1, 'C', True)

            pdf.set_font("Arial", size=10)
            for item in dados:
                if item.get('leitura_agua') is not None:
                    pdf.cell(40, 10, str(item.get('unidade_id', 'N/A')), 1)
                    pdf.cell(90, 10, str(
                        item.get('data_hora_coleta', 'N/A')), 1)
                    pdf.cell(60, 10, f"{item.get('leitura_agua', 0.0):.2f}", 1)
                    pdf.ln()

            pdf.ln(10)

            # --- TABELA 2: GÁS ---
            pdf.set_font("Arial", "B", 12)
            pdf.set_text_color(230, 81, 0)  # Laranja Escuro
            pdf.cell(200, 10, txt="QUADRO DE CONSUMO: GÁS", ln=True, align='L')

            pdf.set_font("Arial", "B", 10)
            pdf.set_text_color(0, 0, 0)
            pdf.set_fill_color(255, 224, 178)  # Fundo Laranja Claro
            pdf.cell(40, 10, "Unidade", 1, 0, 'C', True)
            pdf.cell(90, 10, "Data/Hora Coleta", 1, 0, 'C', True)
            pdf.cell(60, 10, "Leitura (m3)", 1, 1, 'C', True)

            pdf.set_font("Arial", size=10)
            for item in dados:
                if item.get('leitura_gas') is not None:
                    pdf.cell(40, 10, str(item.get('unidade_id', 'N/A')), 1)
                    pdf.cell(90, 10, str(
                        item.get('data_hora_coleta', 'N/A')), 1)
                    pdf.cell(60, 10, f"{item.get('leitura_gas', 0.0):.2f}", 1)
                    pdf.ln()

            caminho_pdf = "relatorio_consumo.pdf"
            pdf.output(caminho_pdf)
            return os.path.abspath(caminho_pdf)
        except Exception as e:
            raise Exception(f"Erro ao gerar PDF: {str(e)}")

    @staticmethod
    def gerar_csv_consumo(dados):
        """Gera um arquivo CSV para integração com planilhas (Excel PT-BR)."""
        try:
            caminho_csv = "dados_consumo.csv"
            campos = ["unidade_id", "leitura_agua",
                      "leitura_gas", "data_hora_coleta"]

            with open(caminho_csv, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=campos, delimiter=';')
                writer.writeheader()
                for item in dados:
                    writer.writerow({k: item.get(k, '') for k in campos})

            return os.path.abspath(caminho_csv)
        except Exception as e:
            raise Exception(f"Erro ao gerar CSV: {str(e)}")

    @staticmethod
    def enviar_relatorios_por_email(pdf_path, csv_path, destinatario=None):
        """Envia os arquivos gerados via SMTP (E-mail)."""
        # --- CONFIGURAÇÕES DO SERVIDOR (variáveis de ambiente) ---
        EMAIL_ORIGEM = os.getenv("EMAIL_USER", "seu_email@gmail.com")
        SENHA_APP = os.getenv("EMAIL_PASS", "sua_senha_app_google")
        EMAIL_DESTINO = os.getenv(
            "EMAIL_DESTINO", destinatario or "escritorio@vivereprudente.com.br")
        destinatario = destinatario or EMAIL_DESTINO

        try:
            msg = EmailMessage()
            msg['Subject'] = f"Relatório de Consumo Água/Gás - {datetime.now().strftime('%m/%Y')}"
            msg['From'] = EMAIL_ORIGEM
            msg['To'] = destinatario
            msg.set_content(
                f"Prezados,\n\nSegue em anexo o relatório de fechamento de leituras do Condomínio Vivere Prudente.\n\nGerado automaticamente pelo AguaFlow.")

            # Anexar PDF
            with open(pdf_path, 'rb') as f:
                msg.add_attachment(f.read(), maintype='application',
                                   subtype='pdf', filename=os.path.basename(pdf_path))

            # Anexar CSV
            with open(csv_path, 'rb') as f:
                msg.add_attachment(
                    f.read(), maintype='text', subtype='csv', filename=os.path.basename(csv_path))

            # Envio via Gmail (exemplo)
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(EMAIL_ORIGEM, SENHA_APP)
                smtp.send_message(msg)

            return True, "Relatórios enviados com sucesso para o escritório!"
        except Exception as e:
            return False, f"Falha no envio do e-mail: {str(e)}"
