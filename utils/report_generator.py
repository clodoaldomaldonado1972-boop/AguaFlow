import csv
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

class ReportGenerator:
    @classmethod
    def gerar_csv(cls, dados, nome_arquivo="relatorio_consumo.csv"):
        """Converte as leituras filtradas em um arquivo CSV."""
        if not dados: return None
        
        caminho = os.path.join("relatorios", nome_arquivo)
        os.makedirs("relatorios", exist_ok=True)
        
        with open(caminho, mode='w', newline='', encoding='utf-8') as f:
            # Usa as chaves do primeiro registro como cabeçalho
            writer = csv.DictWriter(f, fieldnames=dados[0].keys())
            writer.writeheader()
            writer.writerows(dados)
        return caminho

    @classmethod
    def gerar_pdf(cls, dados, titulo="Relatório de Consumo"):
        """Cria um PDF profissional com os dados de Água e Gás do período."""
        if not dados: return None
        
        caminho = os.path.join("relatorios", f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf")
        os.makedirs("relatorios", exist_ok=True)
        
        doc = SimpleDocTemplate(caminho, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Cabeçalho do Documento
        elements.append(Paragraph(titulo, styles['Title']))
        elements.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Preparação da Tabela
        # Definimos os títulos das colunas
        tabela_data = [["Unidade", "Água (m³)", "Gás (m³)", "Tipo", "Data/Hora"]]
        
        for d in dados:
            tabela_data.append([
                d.get('unidade', '-'),
                f"{d.get('leitura_agua', 0):.3f}",
                f"{d.get('leitura_gas', 0):.3f}",
                d.get('tipo', '-'),
                d.get('data_leitura_atual', '-')[:16] # Formata data
            ])
            
        # Estilização da Tabela
        t = Table(tabela_data, hAlign='CENTER')
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2196F3")), # Azul AguaFlow
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey])
        ]))
        
        elements.append(t)
        doc.build(elements)
        return caminho