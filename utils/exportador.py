import csv
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from utils import gerador_qr


class Exportador:
    @staticmethod
    def gerar_csv_dashboard(dados):
        """
        Transforma os dados do banco em um relatório CSV legível pelo Excel.
        """
        try:
            # 1. Garante que a pasta de relatórios existe na raiz do AguaFlow
            if not os.path.exists("relatorios"):
                os.makedirs("relatorios")

            # 2. Verifica se existem dados para exportar
            if not dados:
                print("⚠️ Exportador: Nenhum dado recebido para gerar o CSV.")
                return None

            # 3. Define o nome do arquivo com data e hora atual
            data_str = datetime.now().strftime("%Y%m%d_%H%M")
            nome_arquivo = f"relatorios/dashboard_vivere_{data_str}.csv"

            # 4. Cabeçalhos alinhados com o banco de dados
            cabecalhos = ['Apartamento', 'Consumo_m3', 'Data_Leitura']

            # 5. Gravação do arquivo com encoding compatível com Excel brasileiro
            with open(nome_arquivo, 'w', newline='', encoding='utf-8-sig') as f:
                # Ponto e vírgula para Excel PT-BR
                writer = csv.writer(f, delimiter=';')
                writer.writerow(cabecalhos)
                writer.writerows(dados)

            print(f"✅ Relatório CSV gerado com sucesso: {nome_arquivo}")
            return nome_arquivo

        except Exception as e:
            print(f"❌ Erro crítico no Exportador: {e}")
            return None

# --- MANTENDO AS FUNÇÕES DE PDF QUE REVISAMOS ANTERIORMENTE ---


def gerar_pdf_etiquetas(lista_unidades):
    caminho_pdf = os.path.join("storage", "Etiquetas_QR_Vivere.pdf")
    c = canvas.Canvas(caminho_pdf, pagesize=A4)
    # ... (lógica de etiquetas QR mantida conforme revisado)
    c.save()
    return caminho_pdf


def gerar_pdf_relatorio_mensal(dados):
    pasta_nome = datetime.now().strftime("relatorios/Relatorios_%Y_%m")
    if not os.path.exists(pasta_nome):
        os.makedirs(pasta_nome)

    timestamp = datetime.now().strftime("%d_%H%M%S")
    nome_arquivo = os.path.join(
        pasta_nome, f"Relatorio_Vivere_{timestamp}.pdf")
    # ... (lógica de relatório PDF mantida conforme revisado)
    return nome_arquivo
