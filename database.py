import sqlite3
import datetime


def get_connection():
    """Conexão única padronizada para todo o sistema."""
    return sqlite3.connect("aguaflow.db", check_same_thread=False)


def init_db():
    """Inicializa o banco e as tabelas com suporte a datas."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Criação das tabelas (Dentro da função)
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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_consumo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade TEXT,
            mes_referencia TEXT,
            consumo REAL,
            leitura_final REAL
        )
    """)

    # Migração de coluna (Dentro da função)
    try:
        cursor.execute("ALTER TABLE leituras ADD COLUMN data_anterior TEXT")
    except sqlite3.OperationalError:
        pass

    # --- POPULAÇÃO INICIAL (Lógica Vivere: 166, 165... 11) ---
    cursor.execute("SELECT COUNT(*) FROM leituras")
    count = cursor.fetchone()[0]

    if count == 0:
        print("📁 Banco vazio! Gerando unidades do Vivere (16º ao 1º andar)...")
        unidades = []
        # Loop do andar 16 ao 1
        for andar in range(16, 0, -1):
            # Finais 6 ao 1 (166, 165... 161)
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
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT unidade, leitura_atual, leitura_anterior, data_leitura, data_anterior 
        FROM leituras 
        ORDER BY unidade ASC
    """)
    dados = cursor.fetchall()
    conn.close()
    return dados


def registrar_leitura(id_unidade, valor, status="lido"):
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
    conn = get_connection()
    cursor = conn.cursor()
    # Ordem Vivere Prudente: Do andar 16 para o 1, depois áreas comuns
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
