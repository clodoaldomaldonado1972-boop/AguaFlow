import csv
import os
from datetime import datetime

class Exportador:
    @staticmethod
    def gerar_csv_dashboard(dados):
        """
        Transforma os dados do banco em um relatório CSV legível pelo Excel.
        """
        try:
            # 1. Garante que a pasta de relatórios existe
            if not os.path.exists("relatorios"):
                os.makedirs("relatorios")

            # 2. Verifica se existem dados para exportar (evita arquivo de 1KB vazio)
            if not dados or len(dados) == 0:
                print("⚠️ Exportador: Nenhum dado recebido para gerar o CSV.")
                return None

            # 3. Define o nome do arquivo com data e hora atual
            data_str = datetime.now().strftime("%Y%m%d_%H%M")
            nome_arquivo = f"relatorios/dashboard_vivere_{data_str}.csv"

            # 4. Cabeçalhos (Alinhados com o SELECT do seu Database)
            cabecalhos = ['Apartamento', 'Consumo_m3', 'Data_Leitura']

            # 5. Gravação do arquivo
            # utf-8-sig permite que o Excel brasileiro abra sem erros de acentuação
            with open(nome_arquivo, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')
                writer.writerow(cabecalhos)
                
                # Escreve as linhas de dados vindas do banco
                writer.writerows(dados)

            print(f"✅ Relatório gerado com sucesso: {nome_arquivo}")
            return nome_arquivo

        except Exception as e:
            print(f"❌ Erro crítico no Exportador: {e}")
            return None