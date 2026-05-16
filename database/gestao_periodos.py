import os
from database.database import Database
from utils.backup import executar_backup_seguranca
from relatorio_engine import RelatorioEngine
from utils.email_service import enviar_relatorios_por_email


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

        # 2. Busca leituras do mês corrente
        dados = Database.get_leituras_mes_atual()
        if not dados:
            return False

        # 3. Gera os 4 arquivos (PDF agua, PDF gas, CSV agua, CSV gas)
        arquivos = RelatorioEngine.gerar_todos(dados)
        if not arquivos:
            return False

        # 4. Salva as leituras atuais como referência (leitura anterior) do próximo ciclo
        Database.salvar_referencias_ciclo(dados)

        # 5. Envia todos os arquivos por e-mail
        lista_caminhos = list(arquivos.values())
        enviou = enviar_relatorios_por_email(lista_caminhos)

        if enviou:
            # 6. Sucesso: prepara ciclo seguinte
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
            # Limpa leituras do período mantendo a estrutura
            cursor.execute("""
                UPDATE leituras SET
                leitura_agua = NULL,
                leitura_gas = NULL,
                sincronizado = 0,
                data_leitura_atual = NULL,
                tipo = COALESCE(tipo, 'manual')
            """)
            conn.commit()
        print("SUCESSO: Banco de dados preparado para o novo mês!")
        return True
    except Exception as e:
        print(f"Erro no reset do banco: {e}")
        return False
