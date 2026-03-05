import sqlite3

def get_connection():
    """Estabelece a conexão com o banco de dados SQLite."""
    return sqlite3.connect("aguaflow.db", check_same_thread=False)

def init_db():
    """
    Inicializa o banco de dados, cria as tabelas e popula com as 
    unidades do Vivere Prudente na ordem logística (166 a 11).
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Criação da tabela principal com suporte a Água e Gás
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade TEXT NOT NULL,
            agua_anterior REAL DEFAULT 0.0,
            agua_atual REAL DEFAULT 0.0,
            gas_anterior REAL DEFAULT 0.0,
            gas_atual REAL DEFAULT 0.0,
            status TEXT DEFAULT 'pendente'
        )
    """)
    
    # Verifica se o banco já contém dados para evitar duplicidade
    cursor.execute("SELECT COUNT(*) FROM leituras")
    if cursor.fetchone()[0] == 0:
        unidades = []
        
        # LOGÍSTICA VIVERE: Do andar 16 ao 1, do final 6 ao 1 (Ex: 166, 165... 11)
        for andar in range(16, 0, -1):
            for final in range(6, 0, -1):
                numero_unidade = f"{andar}{final}"
                unidades.append((numero_unidade,))
        
        # Inserção das unidades especiais
        unidades.append(('LAZER',))
        unidades.append(('GERAL',))
        
        cursor.executemany("INSERT INTO leituras (unidade) VALUES (?)", unidades)
        conn.commit()
    conn.close()

def buscar_proximo_pendente():
    """Busca no banco a próxima unidade que ainda não foi lida."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM leituras WHERE status = 'pendente' ORDER BY id ASC LIMIT 1")
    resultado = cursor.fetchone()
    conn.close()
    return resultado

def registrar_leitura(id_unidade, valor, tipo="agua", status="concluido"):
    """Registra o valor lido no banco de dados para a unidade específica."""
    conn = get_connection()
    cursor = conn.cursor()
    coluna = "agua_atual" if tipo == "agua" else "gas_atual"
    cursor.execute(f"UPDATE leituras SET {coluna} = ?, status = ? WHERE id = ?", (valor, status, id_unidade))
    conn.commit()
    conn.close()

def resetar_ciclo():
    """Limpa as leituras e volta o status para pendente em todas as unidades."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE leituras 
        SET agua_atual = 0.0, gas_atual = 0.0, status = 'pendente'
    """)
    conn.commit()
    conn.close()
        