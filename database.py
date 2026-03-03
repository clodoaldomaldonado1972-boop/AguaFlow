import sqlite3  # Usaremos SQLite por ser mais fácil de transportar no PI


def conectar():
    return sqlite3.connect("aguaflow.db", check_same_thread=False)


def criar_tabelas():
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade TEXT NOT NULL,
            leitura_agua REAL,
            leitura_gas REAL,
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def salvar_leitura(unidade, agua, gas):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO leituras (unidade, leitura_agua, leitura_gas)
        VALUES (?, ?, ?)
    """, (unidade, agua, gas))
    conn.commit()
    conn.close()
    print(f"✅ {unidade} salvo com sucesso!")


# Cria o banco assim que o script for rodado
criar_tabelas()


def limpar_banco():
    conn = conectar()
    cursor = conn.cursor()
    # Deleta todos os registros da tabela
    cursor.execute("DELETE FROM leituras")
    conn.commit()
    conn.close()
    print("🧹 Banco de dados limpo com sucesso!")
