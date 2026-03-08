import database as db
import utils


def finalizar_mes_e_enviar(email_destino):
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT unidade, leitura_atual, leitura_anterior, data_leitura FROM leituras WHERE status = 'lido'")
        dados = cursor.fetchall()
        conn.close()

        if not dados:
            return False

        # Gera o PDF do relatório
        pdf = utils.gerar_relatorio_leituras_pdf(dados)

        # Só reseta o banco se o e-mail for enviado
        if utils.enviar_email_com_pdf(email_destino, pdf):
            return resetar_banco_para_novo_mes()
        return False
    except Exception as e:
        print(f"Erro na gestão: {e}")
        return False


def resetar_banco_para_novo_mes():
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        # Move atual para anterior e limpa o resto
        cursor.execute("""
            UPDATE leituras SET 
            leitura_anterior = IFNULL(leitura_atual, leitura_anterior),
            leitura_atual = NULL, status = 'pendente', data_leitura = NULL
        """)
        conn.commit()
        conn.close()
        return True
    except:
        return False
