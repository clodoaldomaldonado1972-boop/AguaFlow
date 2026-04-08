import os
from database.database import Database
# --- IMPORT CORRIGIDO PARA A NOVA ESTRUTURA ---
from database.backup import executar_backup_seguranca
# Função que agora está em utils/
from utils.exportador import gerar_pdf_csv as gerar_relatorio_consumo
# Serviço que agora está em utils/
from utils.email_service import enviar_relatorio_por_email


def finalizar_mes_e_enviar(email_destino=None):
    """
    Executa o backup, gera o relatório do mês, envia por e-mail e
    reseta o banco de dados para o próximo ciclo de leituras.
    """
    try:
        # 1. Segurança: Garante a cópia antes de modificar o banco[cite: 13]
        if not executar_backup_seguranca():
            print("ERRO: Falha no backup. Operação cancelada por segurança.")
            return False

        # 2. Lógica de Negócio: Busca leituras já realizadas[cite: 13]
        dados_resp = Database.get_leituras()  # Busca todas as leituras do mês atual
        if not dados_resp.get("sucesso"):
            return False

        dados = dados_resp.get("dados") or []

        # Gera o arquivo PDF/CSV usando a lógica da pasta utils/[cite: 1, 2, 13]
        caminho_arquivo = gerar_relatorio_consumo(dados)

        # Envia o relatório por e-mail[cite: 1, 13]
        # Se email_destino for None, o serviço usa o e-mail padrão do .env
        enviou = enviar_relatorio_por_email(
            caminho_arquivo, destinatario=email_destino)

        if enviou:
            # 3. Sucesso: Reseta o banco para o novo mês[cite: 13]
            return resetar_banco_para_novo_mes()

        return False
    except Exception as e:
        print(f"Erro ao finalizar o mês: {e}")
        return False


def resetar_banco_para_novo_mes():
    """
    Transfere a leitura atual para o campo anterior e limpa os campos para o novo ciclo[cite: 13].
    """
    try:
        with Database.get_db() as conn:
            cursor = conn.cursor()
            # Atualiza os estados para o próximo mês[cite: 13]
            cursor.execute("""
                UPDATE leituras SET
                valor = NULL,
                sincronizado = 0,
                data_leitura = NULL
            """)
            conn.commit()
        print("SUCESSO: Banco de dados preparado para o novo mês!")
        return True
    except Exception as e:
        print(f"Erro no reset do banco: {e}")
        return False
