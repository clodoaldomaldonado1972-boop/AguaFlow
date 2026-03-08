import sqlite3
import datetime


def get_connection():
    """Conexão única padronizada para todo o sistema."""
    return sqlite3.connect("aguaflow.db", check_same_thread=False)


def init_db():
    """Inicializa o banco e as tabelas com suporte a datas."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Cria a tabela com a estrutura completa (Já incluindo data_anterior)
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

    # 2. Tabela de histórico
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_consumo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade TEXT,
            mes_referencia TEXT,
            consumo REAL,
            leitura_final REAL
        )
    """)

    # --- MIGRAR BANCO EXISTENTE (Caso o usuário já tenha o banco sem a coluna) ---
    try:
        cursor.execute("ALTER TABLE leituras ADD COLUMN data_anterior TEXT")
        print("✅ Coluna 'data_anterior' adicionada com sucesso.")
    except sqlite3.OperationalError:
        # Se cair aqui, é porque a coluna já existe, então não faz nada
        pass

    # --- POPULAÇÃO INICIAL ---
    cursor.execute("SELECT COUNT(*) FROM leituras")
    count = cursor.fetchone()[0]

    if count == 0:
        print("📁 Banco vazio! Gerando unidades...")
        unidades = []
        for andar in range(16, 0, -1):
            for final in range(1, 7):  # Ajustado para 1 a 6
                nome_unidade = f"{andar}{final:02d}"
                unidades.append((nome_unidade, 0.0))

        unidades.append(('LAZER', 0.0))
        unidades.append(('GERAL', 0.0))

        cursor.executemany(
            "INSERT INTO leituras (unidade, leitura_anterior, status) VALUES (?, ?, 'pendente')",
            unidades
        )
        conn.commit()
        print(f"✅ {len(unidades)} unidades inseridas.")

    conn.close()


def buscar_todas_leituras():
    """Busca dados para o relatório incluindo as duas datas."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            unidade, 
            leitura_atual, 
            leitura_anterior, 
            data_leitura,    -- Data Atual
            data_anterior    -- Data Anterior
        FROM leituras 
        ORDER BY unidade ASC
    """)
    dados = cursor.fetchall()
    conn.close()
    return dados


def registrar_leitura(id_unidade, valor, status="lido"):
    conn = get_connection()
    cursor = conn.cursor()
    agora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")  # Formato BR

    cursor.execute("""
        UPDATE leituras 
        SET leitura_atual = ?, status = ?, data_leitura = ? 
        WHERE id = ?
    """, (valor, status, agora, id_unidade))
    conn.commit()
    conn.close()


def resetar_mes_novo():
    """Prepara o banco para o próximo mês movendo datas e valores."""
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
def buscar_proximo_pendente():
    """Busca a próxima unidade que ainda não foi lida no ciclo atual."""
    conn = get_connection()
    cursor = conn.cursor()
    # Busca a primeira unidade onde a leitura_atual ainda é NULA
    cursor.execute("""
        SELECT id, unidade, leitura_anterior 
        FROM leituras 
        WHERE leitura_atual IS NULL 
        AND status = 'pendente' 
        ORDER BY id ASC 
        LIMIT 1
    """)
    res = cursor.fetchone()
    conn.close()
    return res