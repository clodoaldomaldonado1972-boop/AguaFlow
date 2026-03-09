import sqlite3
import datetime


def get_connection():
    """Conexão única padronizada para todo o sistema."""
    # check_same_thread=False é vital para o Flet não travar o banco
    return sqlite3.connect("aguaflow.db", check_same_thread=False)


def init_db():
    """Inicializa o banco e as tabelas com suporte a datas."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Tabela de Leituras Atuais
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

    # 2. Tabela de Histórico (Backup de meses passados)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_consumo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade TEXT,
            mes_referencia TEXT,
            consumo REAL,
            leitura_final REAL
        )
    """)

    # Migração automática se a coluna data_anterior não existir
    try:
        cursor.execute("ALTER TABLE leituras ADD COLUMN data_anterior TEXT")
    except sqlite3.OperationalError:
        pass

    # --- POPULAÇÃO INICIAL (Vivere Prudente: 16º ao 1º andar) ---
    cursor.execute("SELECT COUNT(*) FROM leituras")
    if cursor.fetchone()[0] == 0:
        print("📁 Banco vazio! Gerando unidades do Vivere (16º ao 1º)...")
        unidades = []
        for andar in range(16, 0, -1):
            for final in range(6, 0, -1):
                nome_unidade = f"{andar}{final}"
                unidades.append((nome_unidade, 0.0))

        unidades.append(('LAZER', 0.0))
        unidades.append(('GERAL', 0.0))

        cursor.executemany(
            "INSERT INTO leituras (unidade, leitura_anterior, status) VALUES (?, ?, 'pendente')",
            unidades
        )
        conn.commit()
        print(f"✅ {len(unidades)} unidades inseridas com sucesso.")

    conn.close()


def buscar_todas_leituras():
    """Busca dados para o reports.py na ordem lógica de leitura."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT unidade, leitura_atual, leitura_anterior, data_leitura, data_anterior 
        FROM leituras 
        ORDER BY 
            CASE WHEN unidade GLOB '[0-9]*' THEN 0 ELSE 1 END, 
            CAST(unidade AS INTEGER) DESC
    """)
    dados = cursor.fetchall()
    conn.close()
    return dados


def registrar_leitura(id_unidade, valor, status="lido"):
    """Salva a leitura feita pelo usuário ou QR Code."""
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


def buscar_proximo_pendente():
    """Busca a próxima unidade que o Clodoaldo precisa ler."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, unidade, leitura_anterior 
        FROM leituras 
        WHERE (leitura_atual IS NULL OR leitura_atual = 0)
        ORDER BY 
            CASE WHEN unidade GLOB '[0-9]*' THEN 0 ELSE 1 END, 
            CAST(unidade AS INTEGER) DESC
    """)
    res = cursor.fetchone()
    conn.close()
    return res
