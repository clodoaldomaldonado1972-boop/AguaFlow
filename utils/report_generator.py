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
        if not dados:
            return None
        caminho = os.path.join("relatorios", nome_arquivo)
        os.makedirs("relatorios", exist_ok=True)
        with open(caminho, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=dados[0].keys())
            writer.writeheader()
            writer.writerows(dados)
        return caminho

    @classmethod
    def gerar_pdf(cls, dados, titulo="Relatório de Consumo"):
        if not dados:
            return None
        caminho = os.path.join(
            "relatorios", f"relatorio_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf")
        os.makedirs("relatorios", exist_ok=True)

        doc = SimpleDocTemplate(caminho, pagesize=A4)
        elements = []

        def draw_header(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica-Bold', 14)
            canvas.drawCentredString(A4[0]/2.0, A4[1]-30, titulo)
            canvas.setFont('Helvetica', 10)
            data_str = f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            canvas.drawRightString(A4[0]-40, A4[1]-45, data_str)
            canvas.line(40, A4[1]-50, A4[0]-40, A4[1]-50)
            canvas.restoreState()

        elements.append(Spacer(1, 30))
        tabela_data = [
            ["Unidade", "Água (m³)", "Gás (m³)", "Tipo", "Data/Hora"]]
        for d in dados:
            tabela_data.append([
                d.get('unidade', '-'),
                f"{d.get('leitura_agua') or 0:.3f}",
                f"{d.get('leitura_gas') or 0:.3f}",
                d.get('tipo', '-'),
                d.get('data_leitura_atual', '-')[:16]
            ])

        t = Table(tabela_data, hAlign='CENTER', repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2196F3")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [colors.whitesmoke, colors.lightgrey])
        ]))
        elements.append(t)
        doc.build(elements, onFirstPage=draw_header, onLaterPages=draw_header)
        return caminho
