import sqlite3
import datetime

def get_connection():
    """Conexão única padronizada para todo o sistema."""
    return sqlite3.connect("aguaflow.db", check_same_thread=False)

def init_db():
    """Inicializa o banco e as tabelas se não existirem."""
    conn = get_connection()
    cursor = conn.cursor()

    # Criando a tabela principal (Garantindo a coluna leitura_atual)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade TEXT NOT NULL,
            leitura_anterior REAL DEFAULT 0.0,
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

    # --- VERIFICAÇÃO DE DADOS ---
    cursor.execute("SELECT COUNT(*) FROM leituras")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("📁 Banco vazio! Gerando unidades do 16º ao 1º andar...")
        unidades = []
        for andar in range(16, 0, -1):
            for final in range(6, 0, -1):
                # Usando :02d para ficar 1601, 0101 etc, ou apenas {andar}{final}
                unidades.append((f"{andar}{final}", 0.0))
        
        unidades.append(('LAZER', 0.0))
        unidades.append(('GERAL', 0.0))
        
        cursor.executemany(
            "INSERT INTO leituras (unidade, leitura_anterior, status) VALUES (?, ?, 'pendente')", 
            unidades
        )
        conn.commit()
        print(f"✅ {len(unidades)} unidades inseridas com sucesso!")
    else:
        print(f"✅ Banco carregado: {count} unidades encontradas.")

    conn.close()

def buscar_proximo_pendente():
    conn = get_connection()
    cursor = conn.cursor()
    # A LOGICA: Procura onde a leitura_atual ainda é NULA
    cursor.execute("""
        SELECT id, unidade, leitura_anterior 
        FROM leituras 
        WHERE leitura_atual IS NULL AND status = 'pendente' 
        LIMIT 1
    """)
    res = cursor.fetchone()
    conn.close()
    return res

def buscar_todas_leituras():
    """ESSA É A FUNÇÃO QUE O REPORTS.PY CHAMA"""
    conn = get_connection()
    cursor = conn.cursor()
    # Pegamos os dados e já calculamos o consumo para o PDF
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
def buscar_proximo_pendente():
    conn = get_connection()
    cursor = conn.cursor()
    # Só traz quem REALMENTE não tem leitura_atual
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