import csv
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

class Exportador:
    @staticmethod
    def gerar_csv_dashboard(dados):
        """Transforma os dados do banco em um CSV legível pelo Excel."""
        try:
            if not os.path.exists("relatorios"):
                os.makedirs("relatorios")

            if not dados:
                return None

            data_str = datetime.now().strftime("%Y%m%d_%H%M")
            nome_arquivo = f"relatorios/dashboard_vivere_{data_str}.csv"

            # Cabeçalhos amigáveis para o Excel
            cabecalhos = ['Apartamento', 'Leitura Agua (m3)', 'Leitura Gas (m3)', 'Data/Hora']
            
            with open(nome_arquivo, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';') # Delimitador ';' é melhor para Excel PT-BR
                writer.writerow(cabecalhos)
                
                for item in dados:
                    # AJUSTE CRÍTICO: Mapeamento manual para garantir que os nomes do banco batem
                    writer.writerow([
                        item.get('unidade', 'N/A'),
                        item.get('leitura_agua', 0),
                        item.get('leitura_gas', 0),
                        item.get('data_leitura', 'N/A')
                    ])
            
            return nome_arquivo
        except Exception as e:
            print(f"Erro ao exportar CSV: {e}")
            return None

    @staticmethod
    def gerar_pdf_relatorio_mensal(dados):
        """Gera um PDF formatado com as leituras."""
        try:
            if not os.path.exists("relatorios"):
                os.makedirs("relatorios")

            timestamp = datetime.now().strftime("%d_%H%M%S")
            nome_arquivo = f"relatorios/Relatorio_Vivere_{timestamp}.pdf"

            c = canvas.Canvas(nome_arquivo, pagesize=A4)
            c.setFont("Helvetica-Bold", 16)
            c.drawString(100, 800, "AguaFlow - Relatório Mensal de Consumo")
            
            c.setFont("Helvetica", 12)
            y = 750
            c.drawString(100, y, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            y -= 30
            
            # Cabeçalho da Tabela
            c.drawString(100, y, "Unidade | Água | Gás | Data")
            y -= 20
            c.line(100, y+15, 500, y+15)

            for item in dados:
                if y < 50: # Nova página se acabar o espaço
                    c.showPage()
                    y = 800
                
                linha = f"{item.get('unidade')} | {item.get('leitura_agua')} | {item.get('leitura_gas')} | {item.get('data_leitura')}"
                c.drawString(100, y, linha)
                y -= 20

            c.save()
            return nome_arquivo
        except Exception as e:
            print(f"Erro ao gerar PDF: {e}")
            return None