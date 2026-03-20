import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_API_KEY = os.getenv('SUPABASE_API_KEY')

if not SUPABASE_URL or not SUPABASE_API_KEY:
    raise RuntimeError('Supabase URL/API key not set. Check .env file.')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)


def get_supabase_client() -> Client:
    return supabase


def insert_leitura_supabase(leituras_obj: dict):
    """Insere/atualiza leitura na tabela leituras do Supabase."""
    try:
        # Usamos upsert para permitir reenvio de leituras já existentes, key _id
        result = supabase.table('leituras').upsert(
            leituras_obj, on_conflict='_id').execute()
        if hasattr(result, 'error') and result.error:
            return {'sucesso': False, 'mensagem': str(result.error), 'data': None}

        return {'sucesso': True, 'mensagem': 'Sincronizado com Supabase', 'data': getattr(result, 'data', None)}

    except Exception as e:
        return {'sucesso': False, 'mensagem': f'❌ Erro Supabase: {e}', 'data': None}
