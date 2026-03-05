import sqlite3

def get_connection():
    # Padronizado para 'aguaflow.db' (sem underline) para todas as funções
    return sqlite3.connect("aguaflow.db", timeout=10)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    # AJUSTE: Tabela agora tem 'leitura_atual' e 'leitura_anterior'
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
    
    cursor.execute("SELECT COUNT(*) FROM leituras")
    if cursor.fetchone()[0] == 0:
        # Dados iniciais para teste
        dados = [('101', 'A'), ('102', 'A'), ('201', 'B'), ('202', 'B')]
        cursor.executemany(
            "INSERT INTO leituras (numero, bloco) VALUES (?, ?)", dados)
        print("✅ Unidades de teste inseridas!")
    
    conn.commit()
    conn.close()

def buscar_proximo_pendente():
    conn = get_connection()
    cursor = conn.cursor()
    # Busca o próximo que ainda não foi lido
    cursor.execute(
        "SELECT id, numero, bloco FROM leituras WHERE status = 'Pendente' ORDER BY id LIMIT 1")
    res = cursor.fetchone()
    conn.close()
    return res

def salvar_leitura(id_apto, valor_novo):
    conn = get_connection()
    cursor = conn.cursor()
    
    # LÓGICA DE OURO: Antes de salvar a nova, a atual vira 'anterior'
    cursor.execute("SELECT leitura_atual FROM leituras WHERE id = ?", (id_apto,))
    leitura_antiga = cursor.fetchone()[0]
    
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
    conn = get_connection() # Usando a função padronizada
    cursor = conn.cursor()
    # A ordem que o reports.py espera: 
    # id(0), numero(1), bloco(2), atual(3), anterior(4), status(5)
    cursor.execute("""
        SELECT id, numero, bloco, leitura_atual, leitura_anterior, status 
        FROM leituras
    """)
    dados = cursor.fetchall()
    conn.close()
    return dados
