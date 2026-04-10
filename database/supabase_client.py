import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# --- CONFIGURAÇÃO DE AMBIENTE ---
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_API_KEY = os.getenv('NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY')
DB_PATH = Path(__file__).parent.parent / 'aguaflow.db'  # Caminho do seu SQLite

_supabase_client: Client | None = None


def get_supabase_client():
    global _supabase_client
    if not _supabase_client:
        try:
            if SUPABASE_URL and SUPABASE_API_KEY:
                _supabase_client = create_client(
                    SUPABASE_URL, SUPABASE_API_KEY)
        except Exception as e:
            print(f"⚠️ Erro ao conectar no Supabase: {e}")
    return _supabase_client


def marcar_como_sincronizado_local(id_unidade: str):
    """Executa o comando real no seu arquivo SQLite local."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        # Ajuste o nome da tabela/coluna conforme seu database.py
        cursor.execute(
            "UPDATE medicoes SET sincronizado = 1 WHERE id_unidade = ?", (id_unidade,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Erro ao atualizar SQLite local: {e}")
        return False


def insert_leitura_supabase(id_unidade: str, valor: float, tipo_leitura: str = "Água", leiturista: str = "Zelador"):
    """Envia para nuvem e, se der certo, atualiza o banco local."""
    cliente = get_supabase_client()

    if not cliente:
        return {'sucesso': False, 'mensagem': 'Modo Offline: Sem conexão com Supabase.'}

    try:
        dados = {
            "id_unidade": id_unidade,
            "valor": valor,
            "tipo": tipo_leitura,
            "leiturista": leiturista
        }

        # Realiza o UPSERT no Supabase
        response = cliente.table('medicoes').upsert(dados).execute()

        # Se chegou aqui sem erro, o Supabase aceitou
        if response:
            # AGORA SIM: Chama a função que altera o seu SQLite local
            sucesso_local = marcar_como_sincronizado_local(id_unidade)

            return {
                'sucesso': True,
                'mensagem': 'Sincronizado na Nuvem e no SQLite!' if sucesso_local else 'Sincronizado na Nuvem, mas erro no local.'
            }

    except Exception as e:
        print(f"⚠️ Falha na sincronia: {e}")
        return {'sucesso': False, 'mensagem': f'Erro: {e}'}
