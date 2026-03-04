import sqlite3
from datetime import datetime

# Nome do arquivo do banco de dados (será ignorado pelo seu .gitignore devido ao *.db)
NOME_BANCO = "aguaflow.db"


def conectar():
    """Cria uma conexão com o banco de dados SQLite."""
    return sqlite3.connect(NOME_BANCO)


def init_db():
    """Inicializa o banco de dados e as tabelas necessárias."""
    conn = conectar()
    cursor = conn.cursor()

    # 1. TABELA DE APARTAMENTOS: O cadastro fixo do condomínio
    # status_leitura controla o fluxo: 'Pendente', 'Lido' ou 'Pulado'
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS apartamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero TEXT NOT NULL,
            bloco TEXT,
            status_leitura TEXT DEFAULT 'Pendente'
        )
    ''')

    # 2. TABELA DE LEITURAS: O histórico de cada medição realizada
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            apto_id INTEGER,
            valor_leitura REAL,
            data_hora TEXT,
            metodo TEXT, -- 'QR_OCR' ou 'Manual'
            FOREIGN KEY (apto_id) REFERENCES apartamentos (id)
        )
    ''')

    conn.commit()
    conn.close()

    # Após criar, vamos garantir que existam dados para teste
    popular_apartamentos_exemplo()


def popular_apartamentos_exemplo():
    """Insere apartamentos de teste se a tabela estiver vazia."""
    conn = conectar()
    cursor = conn.cursor()

    # Verifica se já existem apartamentos
    cursor.execute("SELECT COUNT(*) FROM apartamentos")
    if cursor.fetchone()[0] == 0:
        # Lista de aptos para teste (Simulando o Bloco A)
        exemplos = [('101', 'A'), ('102', 'A'), ('103', 'A'), ('104', 'A')]
        cursor.executemany(
            "INSERT INTO apartamentos (numero, bloco) VALUES (?, ?)", exemplos)
        conn.commit()
        print("✅ Apartamentos de teste inseridos!")

    conn.close()


def buscar_proximo_pendente():
    """Busca o primeiro apartamento na fila que ainda não foi lido ou foi pulado."""
    conn = conectar()
    cursor = conn.cursor()
    # Busca o primeiro que não esteja 'Lido'
    cursor.execute(
        "SELECT id, numero, bloco FROM apartamentos WHERE status_leitura != 'Lido' LIMIT 1")
    resultado = cursor.fetchone()
    conn.close()
    return resultado  # Retorna (id, numero, bloco) ou None


def salvar_leitura(apto_id, valor, metodo="QR_OCR"):
    """Registra a leitura e marca o apartamento como Lido."""
    hoje = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = conectar()
    cursor = conn.cursor()

    try:
        # 1. Insere na tabela de histórico
        cursor.execute(
            "INSERT INTO leituras (apto_id, valor_leitura, data_hora, metodo) VALUES (?, ?, ?, ?)",
            (apto_id, valor, hoje, metodo)
        )

        # 2. Atualiza o status no cadastro de apartamentos
        cursor.execute(
            "UPDATE apartamentos SET status_leitura = 'Lido' WHERE id = ?",
            (apto_id,)
        )

        conn.commit()
        print(f"✅ Sucesso: Apto ID {apto_id} registrado com {valor}m³")
    except Exception as e:
        print(f"❌ Erro ao salvar: {e}")
    finally:
        conn.close()


def pular_apartamento(apto_id):
    """Marca o apartamento como 'Pulado' para permitir seguir a sequência."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE apartamentos SET status_leitura = 'Pulado' WHERE id = ?", (apto_id,))
    conn.commit()
    conn.close()
    print(f"⚠️ Apto ID {apto_id} foi marcado como Pulado.")


# Bloco de execução para teste manual
if __name__ == "__main__":
    init_db()
    print("🚀 Banco AguaFlow pronto para uso!")
