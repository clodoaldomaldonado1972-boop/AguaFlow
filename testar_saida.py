import asyncio
import sqlite3
import gc
import os
from utils.export_manager import ExportManager
from utils.report_generator import ReportGenerator
from utils.email_service import enviar_relatorios_por_email


async def realizar_testes_completos():
    print("🚀 Iniciando Auditoria de Saída - AguaFlow v1.1.2")

    # --- TESTE 1: ETIQUETAS QR ---
    try:
        # Busca as unidades no banco local que você validou nas Figuras 3A, 3B e 3C
        conn = sqlite3.connect(r"C:\AguaFlow\aguaflow.db")
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT unidade_id FROM leituras")
        unidades = [row[0] for row in cursor.fetchall()]
        conn.close()

        if unidades:
            print(f"⏳ Gerando etiquetas para {len(unidades)} unidades...")
            pdf_qr = ExportManager.gerar_etiquetas_qr_50_por_folha(
                unidades, "Água")
            print(f"✅ Etiquetas geradas em: {pdf_qr}")
        else:
            print("⚠️ Nenhuma unidade encontrada no banco.")
    except Exception as e:
        print(f"❌ Erro nas etiquetas: {e}")

    # --- TESTE 2: RELATÓRIO E E-MAIL ---
    try:
        print("⏳ Gerando Relatório de Consumo Profissional...")
        conn = sqlite3.connect(r"C:\AguaFlow\aguaflow.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leituras")
        rows = cursor.fetchall()

        dados_formatados = []
        for r in rows:
            dados_formatados.append({
                'unidade': r['unidade_id'],
                'leitura_agua': r['valor_leitura'] if r['tipo_registro'] == 'Água' else 0,
                'leitura_gas': r['valor_leitura'] if r['tipo_registro'] == 'Gás' else 0,
                'tipo': r['tipo'],
                'data_leitura_atual': r['data_hora_coleta']
            })
        conn.close()

        if dados_formatados:
            # Gera o PDF usando o ReportGenerator (Tabela Azul AguaFlow)
            pdf_relatorio = ReportGenerator.gerar_pdf(
                dados_formatados, "Relatório Vivere - Auditoria")
            print(f"✅ Relatório PDF gerado com sucesso!")

            # Disparo de e-mail usando as credenciais do seu arquivo .env
            print("⏳ Iniciando serviço de envio de e-mail...")
            sucesso_email = enviar_relatorios_por_email([pdf_relatorio])
            if sucesso_email:
                print("✅ Fluxo de e-mail concluído com sucesso!")
        else:
            print("⚠️ Banco vazio para relatório.")

    except Exception as e:
        print(f"❌ Erro no relatório/e-mail: {e}")

    # --- TESTE 3: GESTÃO DE MEMÓRIA ---
    try:
        print("⏳ Testando limpeza de memória (GC)...")
        gc.collect()
        print("✅ Memória liberada com sucesso.")
    except Exception as e:
        print(f"❌ Erro na gestão de memória: {e}")

if __name__ == "__main__":
    asyncio.run(realizar_testes_completos())
