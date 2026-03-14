import sqlite3


def init_db():
    conn = sqlite3.connect('aguaflow.db')
    cursor = conn.cursor()
    # Criamos a tabela com o campo 'ordem' para garantir a descida correta
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade TEXT NOT NULL,
            leitura_anterior REAL DEFAULT 0.0,
            leitura_atual REAL,
            tipo TEXT DEFAULT 'AGUA',
            status TEXT DEFAULT 'PENDENTE',
            ordem INTEGER
        )
    ''')
    conn.commit()
    conn.close()

# =============================================================================
# LÓGICA VIVERE PRUDENTE: GERAR LISTA (166 -> 11)
# =============================================================================


def gerar_lista_apartamentos():
    """
    Humanizado: Esta função é o GPS. Ela traça a rota começando do 16º andar,
    passando por todos os 6 aptos de cada andar, até o Geral no Térreo.
    """
    lista_final = []
    ordem_cont = 1

    # Loop dos andares: do 16 ao 1
    for andar in range(16, 0, -1):
        # Loop dos aptos: do 6 ao 1 (Ex: 166, 165, 164, 163, 162, 161)
        for final in range(6, 0, -1):
            unidade = f"{andar}{final}"
            lista_final.append((unidade, 0.0, "AGUA", ordem_cont))
            ordem_cont += 1
            # Se quiser Gás também, adicionamos aqui:
            # lista_final.append((unidade, 0.0, "GAS", ordem_cont))
            # ordem_cont += 1

    # Adiciona as unidades especiais do Térreo
    lista_final.append(("LAZER", 0.0, "AGUA", ordem_cont))
    lista_final.append(("GERAL", 0.0, "AGUA", ordem_cont + 1))

    return lista_final


def buscar_proximo_pendente():
    """
    Humanizado: Ele olha para a 'ordem' e traz o primeiro que ainda não foi lido.
    Isso garante que o app sempre abra no apartamento certo (Retomar leitura).
    """
    conn = sqlite3.connect('aguaflow.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, unidade, leitura_anterior, tipo 
        FROM leituras 
        WHERE status = 'PENDENTE' 
        ORDER BY ordem ASC LIMIT 1
    ''')
    res = cursor.fetchone()
    conn.close()
    return res

# =============================================================================
# O "GRITO" DO SISTEMA: VALIDAR SEQUÊNCIA
# =============================================================================


def verificar_esquecimento_andar(unidade_atual):
    """
    Humanizado: Esta é a função que faz o bipe tocar.
    Ela verifica se existe algum apartamento com ordem menor que o atual
    que ainda está como 'PENDENTE'.
    """
    conn = sqlite3.connect('aguaflow.db')
    cursor = conn.cursor()

    # Busca a ordem da unidade que o leiturista está tentando salvar
    cursor.execute(
        "SELECT ordem FROM leituras WHERE unidade = ?", (unidade_atual,))
    ordem_atual = cursor.fetchone()[0]

    # Procura se ficou alguém para trás
    cursor.execute('''
        SELECT unidade FROM leituras 
        WHERE ordem < ? AND status = 'PENDENTE' 
        ORDER BY ordem DESC LIMIT 1
    ''', (ordem_atual,))

    esquecido = cursor.fetchone()
    conn.close()

    # Retorna o nome da unidade esquecida ou None se estiver tudo ok
    return esquecido[0] if esquecido else None


def registrar_leitura(id_db, valor):
    conn = sqlite3.connect('aguaflow.db')
    cursor = conn.cursor()
    status = 'CONCLUIDO' if valor > 0 else 'VAZIO'
    cursor.execute('''
        UPDATE leituras 
        SET leitura_atual = ?, status = ? 
        WHERE id = ?
    ''', (valor, status, id_db))
    conn.commit()
    conn.close()
