import sqlite3

def get_connection():
    # Adicionamos um timeout de 10 segundos para evitar que o app trave
    return sqlite3.connect("aguaflow.db", timeout=10)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leituras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT,
        bloco TEXT,
        valor REAL,
        status TEXT DEFAULT 'Pendente'
    )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM leituras")
    if cursor.fetchone()[0] == 0:
        dados = [('101', 'A'), ('102', 'A'), ('201', 'B')]
        cursor.executemany(
            "INSERT INTO leituras (numero, bloco) VALUES (?, ?)", dados)
        print("✅ Apartamentos de teste inseridos!")
    conn.commit()
    conn.close()

def buscar_proximo_pendente():
    conn = get_connection()
    cursor = conn.cursor()
    # Adicionamos a busca ordenada por ID para garantir a sequência
    cursor.execute(
        "SELECT id, numero, bloco FROM leituras WHERE status = 'Pendente' ORDER BY id LIMIT 1")
    res = cursor.fetchone()
    conn.close()
    return res

def salvar_leitura(id_apto, valor):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE leituras SET valor = ?, status = 'Lido' WHERE id = ?", (valor, id_apto))
    conn.commit()
    conn.close()

def pular_apartamento(id_apto):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE leituras SET status = 'Pulado' WHERE id = ?", (id_apto,))
    conn.commit()
    conn.close()
    
# No arquivo database.py
def buscar_todos():
    conn = sqlite3.connect("agua_flow.db")
    cursor = conn.cursor()
    # A ORDEM PRECISA SER ESTA:
    cursor.execute("""
        SELECT id, numero, bloco, leitura_atual, leitura_anterior, status 
        FROM leituras
    """)
    dados = cursor.fetchall()
    conn.close()
    return dados

