import os
import sqlite3
import logging
from datetime import datetime
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

        # Testa conexão com uma query simples na tabela de leituras
        response = cliente.table('leituras').select(
            'unidade_id').limit(1).execute()
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


def get_existing_medidor_ids(limit: int = 20):
    """Retorna os IDs de medidores já cadastrados no Supabase."""
    cliente = get_supabase_client()
    if not cliente:
        return []
    try:
        response = cliente.table('medidores').select(
            'unidade_id').limit(limit).execute()
        if getattr(response, 'data', None):
            return [row.get('unidade_id') or row.get('id') for row in response.data if row]
    except Exception as e:
        logger.error(f"Erro ao buscar medidores existentes: {e}")
    return []


def medidor_existe(unidade_id: str) -> bool:
    """Verifica se um medidor já existe na tabela de medidores."""
    cliente = get_supabase_client()
    if not cliente:
        return False
    try:
        response = cliente.table('medidores').select('unidade_id').eq(
            'unidade_id', unidade_id).limit(1).execute()
        return bool(getattr(response, 'data', None))
    except Exception as e:
        logger.error(f"Erro ao verificar medidor {unidade_id}: {e}")
        return False


def ensure_medidor_exists(unidade_id: str) -> bool:
    cliente = get_supabase_client()
    if not cliente:
        return False
    try:
        # Cria a Unidade (Pai) usando id_qrcode conforme o seu Schema Visualizer
        cliente.table('unidades').upsert({
            "id_qrcode": unidade_id,
            "descricao": f"Unidade {unidade_id}"
        }).execute()

        # Cria o Medidor (Filho) vinculado pelo id_qrcode
        cliente.table('medidores').upsert({
            "id_qrcode": unidade_id,
            "unidade_id": unidade_id
        }).execute()
        return True
    except Exception as e:
        logger.error(f"Erro na hierarquia: {e}")
        return False


def marcar_como_sincronizado_local(id_unidade: str):
    """Atualiza o banco local usando o caminho absoluto correto."""
    try:
        # Garante que está usando a classe certa[cite: 1]
        from database.database import Database

        with Database.get_db() as conn:  # Usa o aguaflow.db absoluto[cite: 1]
            cursor = conn.cursor()
            # Tenta marcar como sincronizado. Se a linha não existir, você pode decidir
            # se quer fazer um INSERT aqui também para garantir o backup local.
            cursor.execute("""
                UPDATE leituras 
                SET sincronizado = 1 
                WHERE unidade_id = ?
            """, (id_unidade,))

            # Se não atualizou nada (porque a leitura ainda não existia no local), insere.
            if cursor.rowcount == 0:
                # Aqui você pode adicionar um INSERT se quiser que o local
                # sempre tenha a cópia do que subiu.
                pass

            conn.commit()
            return True
    except Exception as e:
        print(f"❌ Erro ao atualizar SQLite local: {e}")
        return False


def insert_leitura_supabase(id_unidade: str, valor: float, tipo_leitura: str = "Água", leiturista: str = "Zelador", data_hora_coleta: str = None):
    """Envia para nuvem e, se der certo, atualiza o banco local."""
    cliente = get_supabase_client()

    if not cliente:
        return {'sucesso': False, 'mensagem': 'Modo Offline: Sem conexão com Supabase.'}

    if data_hora_coleta is None:
        data_hora_coleta = datetime.now().isoformat(sep=' ', timespec='seconds')

    try:
        dados = {
            "unidade_id": id_unidade,
            "valor_leitura": valor,
            "tipo_registro": tipo_leitura,
            "leiturista": leiturista,
            "data_hora_coleta": data_hora_coleta
        }

        response = cliente.table('leituras').insert(dados).execute()

        if getattr(response, 'data', None) is not None:
            sucesso_local = marcar_como_sincronizado_local(id_unidade)
            return {
                'sucesso': True,
                'mensagem': 'Sincronizado na Nuvem e no SQLite!' if sucesso_local else 'Sincronizado na Nuvem, mas erro no local.'
            }
        else:
            return {
                'sucesso': False,
                'mensagem': 'Falha no envio: resposta vazia do Supabase.'
            }

    except Exception as e:
        print(f"⚠️ Falha na sincronia: {e}")
        return {'sucesso': False, 'mensagem': f'Erro: {e}'}
