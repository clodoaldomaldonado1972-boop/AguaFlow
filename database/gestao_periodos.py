import database as db
import utils
import gerador_pdf
import backup  # <--- Importa o novo arquivo


def finalizar_mes_e_enviar(email):
    # Antes de qualquer coisa, garante a cópia de segurança
    if backup.executar_backup_seguranca():
        # ... aqui continua sua lógica de gerar PDF, enviar e-mail e resetar ...
        pass


def finalizar_mes_e_enviar(email):
    try:
        dados = db.buscar_todas_leituras()
        # Gera o PDF usando o módulo novo
        caminho = gerador_pdf.gerar_relatorio_consumo(dados)

        # Envia usando a função que você me mostrou no utils.py
        enviou = utils.enviar_email_com_pdf(email, caminho)

        if enviou:
            db.resetar_mes_novo()  # Função que limpa 'leituras' e move atual para anterior
            return True
        return False
    except:
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
