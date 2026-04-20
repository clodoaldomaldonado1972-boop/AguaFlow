import csv
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

class Exportador:
    """
    Classe responsável por exportar os dados das medições.
    Lógica: Água é obrigatória, Gás é opcional. 
    Se houver gás, gera arquivos distintos.
    """

    @staticmethod
    def _garantir_pasta_storage():
        """Garante que a pasta de exportação existe na raiz do projeto."""
        caminho_storage = os.path.join(os.getcwd(), "storage")
        if not os.path.exists(caminho_storage):
            os.makedirs(caminho_storage)
        return caminho_storage

    @staticmethod
    def gerar_csv_separados(dados):
        """
        Exporta CSVs distintos para Água e Gás se houver dados de ambos.
        """
        pasta = Exportador._garantir_pasta_storage()
        data_str = datetime.now().strftime("%Y%m%d_%H%M")
        arquivos_gerados = []

        # 1. Processar Relatório de Água (Sempre gerado)
        caminho_agua = os.path.join(pasta, f"Consumo_AGUA_{data_str}.csv")
        with open(caminho_agua, mode='w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['Apartamento', 'Leitura Agua (m3)', 'Data/Hora'])
            for item in dados:
                writer.writerow([item.get('unidade'), item.get('leitura_agua', 0), item.get('data_hora_coleta')])
        arquivos_gerados.append(caminho_agua)

        # 2. Processar Relatório de Gás (Apenas se houver leituras > 0)
        tem_gas = any(float(item.get('leitura_gas', 0) or 0) > 0 for item in dados)
        if tem_gas:
            caminho_gas = os.path.join(pasta, f"Consumo_GAS_{data_str}.csv")
            with open(caminho_gas, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(['Apartamento', 'Leitura Gas (m3)', 'Data/Hora'])
                for item in dados:
                    if float(item.get('leitura_gas', 0) or 0) > 0:
                        writer.writerow([item.get('unidade'), item.get('leitura_gas'), item.get('data_hora_coleta')])
            arquivos_gerados.append(caminho_gas)

        return arquivos_gerados

    @staticmethod
    def gerar_pdf_relatorio_mensal(dados):
        """
        Gera PDFs distintos para Água e Gás conforme a regra de obrigatoriedade.
        """
        pasta = Exportador._garantir_pasta_storage()
        timestamp = datetime.now().strftime("%d_%m_%Y")
        relatorios_finais = []

        # --- FUNÇÃO INTERNA PARA DESENHAR PDF ---
        def criar_pdf_tipo(tipo_nome, chave_dado, unidade_medida):
            nome_arq = os.path.join(pasta, f"Relatorio_{tipo_nome.upper()}_{timestamp}.pdf")
            c = canvas.Canvas(nome_arq, pagesize=A4)
            width, height = A4
            
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(width/2, height - 50, f"RELATÓRIO MENSAL - {tipo_nome.upper()}")
            c.setFont("Helvetica", 10)
            c.drawCentredString(width/2, height - 70, f"Vivere Prudente | Gerado em: {datetime.now().strftime('%d/%m/%Y')}")
            
            y = height - 110
            c.setFont("Helvetica-Bold", 11)
            c.drawString(70, y, "Unidade")
            c.drawString(200, y, f"Leitura ({unidade_medida})")
            c.drawString(350, y, "Data/Hora")
            c.line(70, y-5, 530, y-5)
            y -= 25

            c.setFont("Helvetica", 10)
            for item in dados:
                valor = item.get(chave_dado)
                # No caso do gás, pula se estiver vazio
                if tipo_nome.upper() == "GAS" and (valor is None or float(valor) == 0):
                    continue
                
                if y < 50:
                    c.showPage()
                    y = height - 50
                
                c.drawString(70, y, str(item.get('unidade', 'N/A')))
                c.drawString(200, y, str(valor if valor is not None else "0.00"))
                c.drawString(350, y, str(item.get('data_hora_coleta', 'N/A')))
                y -= 18
            
            c.save()
            return nome_arq

        # Gerar sempre o de Água
        relatorios_finais.append(criar_pdf_tipo("Agua", "leitura_agua", "m³"))

        # Gerar o de Gás apenas se houver dados
        if any(float(item.get('leitura_gas', 0) or 0) > 0 for item in dados):
            relatorios_finais.append(criar_pdf_tipo("Gas", "leitura_gas", "m³"))

        return relatorios_finais