import os
import sqlite3
import logging
from pathlib import Path
from database.database import get_supabase_client

# Logger dedicado para erros de sincronização
SYNC_LOG_DIR = Path(__file__).parent.parent / "storage" / "logs_sync"
SYNC_LOG_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

# DB_PATH para operações locais
DB_PATH = Path(__file__).parent.parent / 'aguaflow.db'


def testar_conexao_supabase():
    """
    Testa a conexão com o Supabase sem realizar operações.
    Retorna dict com {'conectado': bool, 'erro': str ou None}
    """
    try:
        cliente = get_supabase_client()
        if not cliente:
            return {'conectado': False, 'erro': 'Cliente não inicializado (verifique .env)'}

        # Testa conexão com uma query simples
        response = cliente.table('medicoes').select('id').limit(1).execute()
        return {'conectado': True, 'erro': None}

    except Exception as e:
        erro_str = str(e)
        logger.error(f"Teste de conexão falhou: {erro_str}")

        # Classifica o tipo de erro para diagnóstico
        if 'NetworkError' in erro_str or 'Failed to fetch' in erro_str:
            return {'conectado': False, 'erro': 'Sem conexão de internet'}
        elif '401' in erro_str or 'Unauthorized' in erro_str:
            return {'conectado': False, 'erro': 'Credenciais inválidas (401)'}
        elif '403' in erro_str:
            return {'conectado': False, 'erro': 'Acesso negado (403)'}
        else:
            return {'conectado': False, 'erro': erro_str}


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
