#!/usr/bin/env python3
"""
Script para popular as 96 unidades na tabela 'unidades' do SQLite local e do Supabase.
Unidades: Apto 01 ao Apto 96 (ordenados por andar e apartamento)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Importar banco local
from database.database import Database

# Gerar lista das 96 unidades (16 andares x 6 apartamentos por andar)
# Formato: Apto 161, Apto 162, ..., Apto 166, Apto 151, ..., Apto 101
def gerar_unidades():
    """Gera as 96 unidades do prédio (16 andares, 6 aptos por andar)."""
    unidades = []
    for andar in range(16, 0, -1):  # Do 16º ao 1º andar
        for apto in range(1, 7):     # Aptos 1 a 6 por andar
            unidades.append(f"Apto {andar}{apto}")
    return unidades


def popular_sqlite():
    """Popula a tabela 'unidades' no SQLite local."""
    print("=" * 60)
    print("POPULANDO BANCO LOCAL (SQLite)")
    print("=" * 60)

    # Inicializa o banco (cria tabelas se não existirem)
    Database.init_db()
    print("[OK] Banco SQLite inicializado")

    # Gerar unidades
    unidades = gerar_unidades()
    print(f"[OK] {len(unidades)} unidades geradas")

    # Inserir no banco
    with Database.get_db() as conn:
        cursor = conn.cursor()

        # Contar existentes
        cursor.execute("SELECT COUNT(*) FROM unidades")
        count_antes = cursor.fetchone()[0]
        print(f"    Unidades existentes: {count_antes}")

        # Inserir ou ignorar
        cursor.executemany(
            "INSERT OR IGNORE INTO unidades (id) VALUES (?)",
            [(u,) for u in unidades]
        )
        conn.commit()

        # Contar após inserção
        cursor.execute("SELECT COUNT(*) FROM unidades")
        count_depois = cursor.fetchone()[0]
        print(f"    Unidades após inserção: {count_depois}")
        print(f"    Novas unidades inseridas: {count_depois - count_antes}")

    print("\n[OK] SQLite populado com sucesso!")
    return unidades


def popular_supabase(unidades):
    """Popula a tabela 'unidades' no Supabase."""
    print("\n" + "=" * 60)
    print("POPULANDO SUPABASE (Nuvem)")
    print("=" * 60)

    SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
    SUPABASE_KEY = os.getenv('NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY')

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("[ERRO] Credenciais do Supabase não configuradas")
        return False

    try:
        from supabase import create_client
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("[OK] Cliente Supabase criado")

        # Verificar estrutura da tabela
        try:
            response = client.table('unidades').select('*').limit(1).execute()
            print("[OK] Tabela 'unidades' acessível")
            if response.data:
                colunas = list(response.data[0].keys())
                print(f"    Colunas disponíveis: {colunas}")
        except Exception as e:
            erro_str = str(e)
            if "Could not find the table" in erro_str:
                print("[ERRO] Tabela 'unidades' não existe no Supabase")
                print("\nExecute no SQL Editor do Supabase:")
                print("-" * 40)
                print("""CREATE TABLE unidades (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMPTZ DEFAULT NOW()
);""")
                print("-" * 40)
                return False
            elif "does not exist" in erro_str:
                print("[ERRO] Coluna não encontrada - schema pode estar diferente")
                print("\nSugestão: Verifique o schema da tabela no Supabase")
                return False
            elif "column" in erro_str and "does not exist" in erro_str:
                print("[ALERTA] Tabela existe mas sem colunas definidas")
                print("\nExecute no SQL Editor do Supabase para criar a coluna:")
                print("-" * 40)
                print("""-- Adiciona coluna de identificador
ALTER TABLE unidades ADD COLUMN id TEXT PRIMARY KEY;
ALTER TABLE unidades ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW();""")
                print("-" * 40)
                return False
            raise

        # Contar existentes e descobrir schema
        response = client.table('unidades').select('*', count='exact').limit(1).execute()
        count_antes = response.count if hasattr(response, 'count') else 0

        # Descobrir colunas disponíveis
        colunas_validas = []
        if response.data:
            colunas_validas = list(response.data[0].keys())
            print(f"    Colunas disponíveis: {colunas_validas}")

        print(f"    Unidades existentes: {count_antes}")

        # Determinar qual coluna usar para o identificador
        coluna_id = None
        for candidata in ['id', 'unidade', 'nome', 'nome_unidade', 'apartamento']:
            if candidata in colunas_validas:
                coluna_id = candidata
                break

        if not coluna_id and colunas_validas:
            for col in colunas_validas:
                if col not in ['created_at', 'updated_at', 'id']:
                    coluna_id = col
                    break

        if not coluna_id:
            print("\n[ERRO] Nenhuma coluna válida encontrada para inserção")
            return False

        print(f"    Coluna usada para identificador: {coluna_id}")

        # Inserir unidades (UPSERT para evitar duplicatas)
        inseridas = 0
        for unidade in unidades:
            try:
                client.table('unidades').upsert({
                    coluna_id: unidade
                }, on_conflict=coluna_id).execute()
                inseridas += 1
            except Exception as e:
                print(f"    [!] Erro ao inserir {unidade}: {e}")

        print(f"    Unidades processadas: {inseridas}")
        print("\n[OK] Supabase populado com sucesso!")
        return True

    except Exception as e:
        print(f"\n[ERRO] Falha ao conectar no Supabase: {e}")
        return False


def main():
    """Executa o processo completo de população."""
    print("\n" + "=" * 60)
    print("SCRIPT DE POPULAÇÃO - UNIDADES VIVERE PRUDENTE")
    print("=" * 60)

    # 1. Popular SQLite
    unidades = popular_sqlite()

    # 2. Popular Supabase
    sucesso_cloud = popular_supabase(unidades)

    # Resultado final
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    print(f"Total de unidades: {len(unidades)}")
    print(f"SQLite local: [OK]")
    print(f"Supabase nuvem: [{'OK' if sucesso_cloud else 'FALHOU'}]")

    if sucesso_cloud:
        print("\n[SUCCESS] Processo concluído!")
        return 0
    else:
        print("\n[WARNING] Processo parcial - Supabase pendente")
        return 1


if __name__ == "__main__":
    sys.exit(main())
