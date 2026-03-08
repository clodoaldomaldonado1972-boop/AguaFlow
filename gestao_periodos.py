# No topo do arquivo gestao_periodos.py
import database as db
import utils
import flet as ft
from datetime import datetime

def finalizar_mes_e_enviar(email_destino):
    """
    Gera o relatório do mês, envia por e-mail e, se tiver sucesso,
    prepara o banco para o novo mês movendo os dados para o histórico.
    """
    try:
        # 1. Busca os dados atuais para o relatório
        conn = db.get_connection()
        cursor = conn.cursor()
        # Pegamos apenas quem já foi lido para o relatório mensal
        cursor.execute("""
            SELECT unidade, leitura_atual, leitura_anterior, data_leitura 
            FROM leituras 
            WHERE status = 'lido'
        """)
        dados_concluidos = cursor.fetchall()
        conn.close()

        if not dados_concluidos:
            print("⚠️ Erro: Não há leituras concluídas para gerar o relatório.")
            return False

        # 2. Gera o arquivo PDF (usando a função do seu utils.py)
        caminho_pdf = utils.gerar_relatorio_leituras_pdf(dados_concluidos)
        print(f"📄 PDF Gerado: {caminho_pdf}")

        # 3. Tenta enviar o e-mail
        print(f"📧 Enviando para {email_destino}...")
        enviou_ok = utils.enviar_email_com_pdf(email_destino, caminho_pdf)

        if enviou_ok:
            print("✅ E-mail enviado! Agora vamos preparar o banco para o novo mês.")
            # 4. Só faz o reset se o e-mail chegar no destino
            return executar_virada_de_mes()
        else:
            print("❌ Falha no envio do e-mail. O banco NÃO foi resetado.")
            return False

    except Exception as e:
        print(f"❌ Erro crítico no gestao_periodos: {e}")
        return False

def executar_virada_de_mes():
    """
    Move a leitura atual para a coluna 'anterior' (histórico)
    e limpa os campos para o novo ciclo.
    """
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # A mágica acontece aqui: 
        # leitura_anterior recebe o valor que você acabou de medir (leitura_atual)
        cursor.execute("""
            UPDATE leituras 
            SET 
                leitura_anterior = IFNULL(leitura_atual, leitura_anterior),
                leitura_atual = NULL,
                status = 'pendente', 
                data_leitura = NULL
        """)
        
        conn.commit()
        conn.close()
        print("🚀 BANCO RESETADO: Tudo pronto para a nova medição!")
        return True
    except Exception as e:
        print(f"❌ Erro ao resetar banco: {e}")
        return False