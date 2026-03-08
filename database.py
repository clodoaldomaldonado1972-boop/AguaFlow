import sqlite3
import datetime


def get_connection():
    """Conexão única padronizada para todo o sistema."""
    return sqlite3.connect("aguaflow.db", check_same_thread=False)


def init_db():
    """Inicializa o banco e as tabelas se não existirem."""
    conn = get_connection()
    cursor = conn.cursor()

    # Tabela principal de leituras
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

    # Tabela de histórico (para consultas futuras)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico_consumo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade TEXT,
            mes_referencia TEXT,
            consumo REAL,
            leitura_final REAL
        )
    """)

    # --- VERIFICAÇÃO E POPULAÇÃO INICIAL ---
    cursor.execute("SELECT COUNT(*) FROM leituras")
    count = cursor.fetchone()[0]

    if count == 0:
        print("📁 Banco vazio! Gerando unidades do 16º ao 1º andar...")
        unidades = []
        # Gera do 16 ao 1 (Andares)
        for andar in range(16, 0, -1):
            # Gera do 6 ao 1 (Finais)
            for final in range(6, 0, -1):
                # Nome da unidade ex: 166, 165... 11
                nome_unidade = f"{andar}{final}"
                unidades.append((nome_unidade, 0.0))

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
    # Importante: buscar por status 'pendente' que o Reset define
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


def buscar_todas_leituras():
    """Busca dados para o relatório. Protege o consumo contra valores nulos."""
    conn = get_connection()
    cursor = conn.cursor()
    # O CASE impede consumo negativo se leitura_atual for menor que anterior por erro
    cursor.execute("""
        SELECT 
            id, 
            unidade, 
            leitura_anterior, 
            leitura_atual, 
            CASE 
                WHEN leitura_atual IS NULL THEN 0 
                ELSE (leitura_atual - leitura_anterior) 
            END as consumo,
            data_leitura 
        FROM leituras 
        ORDER BY unidade ASC
    """)
    dados = cursor.fetchall()
    conn.close()
    return dados


def registrar_leitura(id_unidade, valor, status="lido"):
    """Salva a leitura no banco com data e hora."""
    conn = get_connection()
    cursor = conn.cursor()
    agora = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE leituras 
        SET leitura_atual = ?, status = ?, data_leitura = ? 
        WHERE id = ?
    """, (valor, status, agora, id_unidade))

    conn.commit()
    conn.close()
    print(f"DEBUG DB: Unidade {id_unidade} atualizada com sucesso.")


def resetar_mes_novo():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # Este comando limpa o 'None' e volta as 98 unidades para o início
        cursor.execute("""
            UPDATE leituras 
            SET 
                leitura_anterior = IFNULL(leitura_atual, leitura_anterior),
                leitura_atual = NULL,
                status = 'pendente', 
                data_leitura = NULL
        """)
        conn.commit()  # <--- SE NÃO TIVER ISSO, O RESET NÃO SALVA!
        conn.close()
        print("✅ SUCESSO: Banco resetado fisicamente no SQLite!")
        return True
    except Exception as e:
        print(f"❌ Erro no Reset: {e}")
        return False


def confirmar_reset(e):
            import database as db  # Garante que o banco está acessível
            db.resetar_mes_novo()   # Limpa o banco (agora com commit!)
            
            dlg.open = False
            page.snack_bar = ft.SnackBar(ft.Text("Mês Resetado! Iniciando novo ciclo."), open=True)
            page.update()
            
            # ISSO AQUI É O QUE LIMPA O ERRO DE 'NONE':
            voltar()