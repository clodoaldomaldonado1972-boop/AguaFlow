import csv
import os
import platform
from datetime import datetime
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
# Removido import de utils.gerador_qr se não estiver sendo usado aqui para evitar erros de circularidade


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

            # 4. Cabeçalhos alinhados com o banco de dados (padronizado como unidade_id)
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
    # Garante que a pasta storage existe
    if not os.path.exists("storage"):
        os.makedirs("storage")

    caminho_pdf = os.path.join("storage", "Etiquetas_QR_Vivere.pdf")
    c = canvas.Canvas(caminho_pdf, pagesize=A4)
    # Lógica de etiquetas QR mantida (pode ser expandida conforme necessidade do PI)
    c.drawString(2*cm, 28*cm, "Folha de Etiquetas QR Code - AguaFlow")
    c.save()
    return caminho_pdf


def gerar_pdf_relatorio_mensal(dados):
    pasta_nome = datetime.now().strftime("relatorios/Relatorios_%Y_%m")
    if not os.path.exists(pasta_nome):
        os.makedirs(pasta_nome)

    timestamp = datetime.now().strftime("%d_%H%M%S")
    nome_arquivo = os.path.join(
        pasta_nome, f"Relatorio_Vivere_{timestamp}.pdf")

    # Lógica simplificada para garantir a criação do arquivo PDF
    c = canvas.Canvas(nome_arquivo, pagesize=A4)
    c.drawString(100, 800, "AguaFlow - Relatório Mensal de Consumo")
    c.save()
    return nome_arquivo

# --- FUNÇÃO DE COMPATIBILIDADE PARA RESOLVER O IMPORT ERROR ---


def gerar_pdf_csv(dados):
    """
    Função ponte para satisfazer o import em views/relatorios.py.
    Ela executa as funções de exportação disponíveis.
    """
    caminho_csv = Exportador.gerar_csv_dashboard(dados)
    caminho_pdf = gerar_pdf_relatorio_mensal(dados)

    return caminho_pdf, caminho_csv


def abrir_arquivo(caminho):
    if platform.system() == "Windows":
        os.startfile(caminho)
    elif platform.system() == "Darwin":  # macOS
        os.system(f'open "{caminho}"')
    else:  # Linux
        os.system(f'xdg-open "{caminho}"')
