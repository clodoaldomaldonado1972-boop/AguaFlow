import database as db
import utils
import gerador_pdf
import backup  # <--- Importa o novo arquivo


def finalizar_mes_e_enviar(email):
    """
    Executa o backup, gera o relatório do mês, envia por e-mail e
    reseta o banco de dados para o próximo ciclo de leituras.
    """
    try:
        # 1. Garante a cópia de segurança antes de qualquer modificação
        if not backup.executar_backup_seguranca():
            # Se o backup falhar, não continua para não arriscar os dados.
            return False

        # 2. Lógica de negócio: gerar PDF e enviar e-mail
        dados = db.buscar_todas_leituras()
        caminho = gerador_pdf.gerar_relatorio_consumo(dados)
        enviou = utils.enviar_email_com_pdf(email, caminho)

        if enviou:
            # 3. Se o envio foi bem-sucedido, reseta o banco para o novo mês.
            resetar_banco_para_novo_mes()
            return True
        return False
    except Exception as e:
        print(f"Erro ao finalizar o mês: {e}")
        return False


def resetar_banco_para_novo_mes():
    conn = None
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE leituras SET
            leitura_anterior = IFNULL(leitura_atual, leitura_anterior),
            leitura_atual = NULL,
            status = 'PENDENTE',
            data_leitura = NULL
        """)
        conn.commit()
        conn.close()
        conn = None
        return True
    except Exception as e:
        print(f"Erro no reset: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()
