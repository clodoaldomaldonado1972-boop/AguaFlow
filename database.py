import sqlite3
import datetime


def get_connection():
    """Conexão única padronizada para todo o sistema."""
    return sqlite3.connect("aguaflow.db", check_same_thread=False)


def init_db():
    """Inicializa o banco e as tabelas com suporte a datas."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Tabela de Leituras (NOME PADRONIZADO: leituras)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade TEXT NOT NULL,
            leitura_anterior REAL DEFAULT 0.0,
            data_anterior TEXT,
            leitura_atual REAL DEFAULT NULL, 
            status TEXT DEFAULT 'pendente',
            data_leitura TEXT
        )
    """)

    # 2. Tabela de Histórico
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_consumo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade TEXT,
            mes_referencia TEXT,
            consumo REAL,
            leitura_final REAL
        )
    """)

    # População inicial (Vivere Prudente: 16º ao 1º andar)
    cursor.execute("SELECT COUNT(*) FROM leituras")
    if cursor.fetchone()[0] == 0:
        print("📁 Gerando unidades do Vivere (16º ao 1º)...")
        unidades = []
        for andar in range(16, 0, -1):
            for final in range(6, 0, -1):
                unidades.append((f"{andar}{final}", 0.0))
        unidades.append(('LAZER', 0.0))
        unidades.append(('GERAL', 0.0))

        cursor.executemany(
            "INSERT INTO leituras (unidade, leitura_anterior, status) VALUES (?, ?, 'pendente')",
            unidades
        )
        conn.commit()

    conn.close()


def buscar_proximo_pendente():
    """Busca a próxima unidade que ainda não foi lida ou pulada."""
    conn = get_connection()
    cursor = conn.cursor()
    # BUSCA APENAS QUEM ESTÁ COM STATUS 'pendente'
    cursor.execute("""
        SELECT id, unidade, leitura_anterior 
        FROM leituras 
        WHERE status = 'pendente'
        ORDER BY id ASC LIMIT 1
    """)
    res = cursor.fetchone()
    conn.close()
    return res


def registrar_leitura(id_unidade, valor, status='concluido'):
    """Salva a leitura e muda o status para sair da fila de pendentes."""
    conn = get_connection()
    cursor = conn.cursor()
    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    cursor.execute("""
        UPDATE leituras 
        SET leitura_atual = ?, status = ?, data_leitura = ? 
        WHERE id = ?
    """, (valor, status, agora, id_unidade))
    conn.commit()
    conn.close()


def resetar_mes_novo():
    """Prepara o banco para o próximo mês de leitura."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE leituras 
            SET 
                leitura_anterior = IFNULL(leitura_atual, leitura_anterior),
                data_anterior = IFNULL(data_leitura, data_anterior),
                leitura_atual = NULL,
                status = 'pendente', 
                data_leitura = NULL
        """)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erro no Reset: {e}")
        return False


def buscar_todas_leituras():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT unidade, leitura_atual, leitura_anterior, data_leitura, data_anterior FROM leituras")
    dados = cursor.fetchall()
    conn.close()
    return dados
