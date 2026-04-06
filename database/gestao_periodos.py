from database.database import Database
from database.backup import executar_backup_seguranca
# Correção dos caminhos que o Amazon Q marcou como inexistentes
from views.reports import gerar_relatorio_consumo
from views.utils.email_service import enviar_relatorio_por_email


def finalizar_mes_e_enviar(email):
    """
    Executa o backup, gera o relatório do mês, envia por e-mail e
    reseta o banco de dados para o próximo ciclo de leituras.
    """
    try:
        # 1. Garante a cópia de segurança antes de qualquer modificação
        if not executar_backup_seguranca():
            # Se o backup falhar, não continua para não arriscar os dados.
            return False

        # 2. Lógica de negócio: gerar PDF e enviar e-mail
        dados_resp = Database.get_leituras(sincronizado=1)
        if not dados_resp.get("sucesso"):
            return False

        dados = dados_resp.get("dados") or []
        caminho = gerar_relatorio_consumo(dados)

        # 'email' mantido por compatibilidade de assinatura;
        # o destinatário é lido do .env no email_service.py.
        enviou = enviar_relatorio_por_email(caminho)

        if enviou:
            # 3. Se o envio foi bem-sucedido, reseta o banco para o novo mês.
            resetar_banco_para_novo_mes()
            return True
        return False
    except Exception as e:
        print(f"Erro ao finalizar o mês: {e}")
        return False


def resetar_banco_para_novo_mes():
    try:
        with Database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE leituras SET
                leitura_anterior = IFNULL(leitura_atual, leitura_anterior),
                leitura_atual = NULL,
                status = 'PENDENTE',
                data_leitura = NULL
            """)
            conn.commit()
        return True
    except Exception as e:
        print(f"Erro no reset: {e}")
        return False
