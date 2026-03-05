import sqlite3

def get_connection():
    # Padronizado para 'aguaflow.db' para todas as funções
    return sqlite3.connect("aguaflow.db", timeout=10)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    # Criando a tabela com as colunas necessárias para o novo relatório
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leituras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT,
        bloco TEXT,
        leitura_atual REAL DEFAULT 0,
        leitura_anterior REAL DEFAULT 0,
        status TEXT DEFAULT 'Pendente'
    )
    """)
    
    # Inserindo dados iniciais se o banco estiver vazio
    cursor.execute("SELECT COUNT(*) FROM leituras")
    if cursor.fetchone()[0] == 0:
        dados = [('101', 'A'), ('102', 'A'), ('201', 'B')]
        cursor.executemany(
            "INSERT INTO leituras (numero, bloco) VALUES (?, ?)", dados)
        print("✅ Unidades de teste inseridas!")
    
    conn.commit()
    conn.close()

# --- ATENÇÃO: Esta função deve ficar fora da init_db (sem espaços extras) ---
def buscar_proximo_pendente():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, numero, bloco FROM leituras WHERE status = 'Pendente' ORDER BY id LIMIT 1")
    res = cursor.fetchone()
    conn.close()
    return res

def salvar_leitura(id_apto, valor_novo):
    conn = get_connection()
    cursor = conn.cursor()
    
    # Busca o valor que era 'atual' para ele virar 'anterior'
    cursor.execute("SELECT leitura_atual FROM leituras WHERE id = ?", (id_apto,))
    resultado = cursor.fetchone()
    leitura_antiga = resultado[0] if resultado else 0
    
    cursor.execute("""
        UPDATE leituras 
        SET leitura_anterior = ?, leitura_atual = ?, status = 'Lido' 
        WHERE id = ?
    """, (leitura_antiga, valor_novo, id_apto))
    
    conn.commit()
    conn.close()

def pular_apartamento(id_apto):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE leituras SET status = 'Pulado' WHERE id = ?", (id_apto,))
    conn.commit()
    conn.close()

def buscar_todos():
    conn = get_connection()
    cursor = conn.cursor()
    # Ordem exigida pelo reports.py: id, numero, bloco, atual, anterior, status
    cursor.execute("""
        SELECT id, numero, bloco, leitura_atual, leitura_anterior, status 
        FROM leituras
    """)
    dados = cursor.fetchall()
    conn.close()
    return dados
