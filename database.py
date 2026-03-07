import sqlite3
import datetime


def get_connection():
    """Conexão única padronizada para todo o sistema."""
    return sqlite3.connect("aguaflow.db", check_same_thread=False)


def init_db():
    """Inicializa o banco e as tabelas se não existirem."""
    conn = get_connection()
    cursor = conn.cursor()

    # Criando a tabela principal
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade TEXT NOT NULL,
            leitura_anterior REAL DEFAULT 0.0,
            leitura_atual REAL,
            status TEXT DEFAULT 'pendente',
            data_leitura TEXT
        )
    """)

    # Criando a tabela de histórico
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_consumo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade TEXT,
            mes_referencia TEXT,
            consumo REAL,
            leitura_final REAL
        )
    """)

    # Popula se estiver vazio (Apartamentos do 16 ao 1)
    cursor.execute("SELECT COUNT(*) FROM leituras")
    if cursor.fetchone()[0] == 0:
        unidades = []
        for andar in range(16, 0, -1):
            for final in range(6, 0, -1):
                unidades.append((f"{andar}{final}", 0.0))
        unidades.append(('LAZER', 0.0))
        unidades.append(('GERAL', 0.0))
        cursor.executemany(
            "INSERT INTO leituras (unidade, leitura_anterior) VALUES (?, ?)", unidades)
        conn.commit()
    conn.close()


def buscar_proximo_pendente():
    conn = get_connection()
    cursor = conn.cursor()
    # Busca unidade onde leitura_atual é NULL e status não é 'pulado'
    cursor.execute(
        "SELECT id, unidade, leitura_anterior FROM leituras WHERE leitura_atual IS NULL AND status = 'pendente' LIMIT 1")
    res = cursor.fetchone()
    conn.close()
    return res


def registrar_leitura(id_unidade, valor, status="lido"):
    conn = get_connection()
    cursor = conn.cursor()
    data_hoje = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        UPDATE leituras 
        SET leitura_atual = ?, status = ?, data_leitura = ? 
        WHERE id = ?
    """, (valor, status, data_hoje, id_unidade))
    conn.commit()
    conn.close()


def buscar_todas_leituras():
    """ESSA É A FUNÇÃO QUE O REPORTS.PY CHAMA"""
    conn = get_connection()
    cursor = conn.cursor()
    # Calculamos o consumo direto na Query para o PDF não vir vazio
    cursor.execute("""
        SELECT 
            id, 
            unidade, 
            leitura_anterior, 
            leitura_atual, 
            (IFNULL(leitura_atual, 0) - leitura_anterior) as consumo,
            data_leitura 
        FROM leituras 
        ORDER BY unidade ASC
    """)
    dados = cursor.fetchall()
    conn.close()
    return dados


def fechar_mes_e_resetar():
    conn = get_connection()
    cursor = conn.cursor()
    mes_ano = datetime.datetime.now().strftime("%m/%Y")

    cursor.execute("""
        INSERT INTO historico_consumo (unidade, mes_referencia, consumo, leitura_final)
        SELECT unidade, ?, (leitura_atual - leitura_anterior), leitura_atual 
        FROM leituras WHERE status = 'lido'
    """, (mes_ano,))

    cursor.execute("""
        UPDATE leituras 
        SET leitura_anterior = CASE WHEN status = 'lido' THEN leitura_atual ELSE leitura_anterior END,
            leitura_atual = NULL,
            status = 'pendente',
            data_leitura = NULL
    """)
    conn.commit()
    conn.close()
