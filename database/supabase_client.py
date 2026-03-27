import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Força a busca do .env na raiz C:\ÁguaFlow\
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Ajustado para os nomes que estão no seu arquivo .env
SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_API_KEY = os.getenv('NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY')

if not SUPABASE_URL or not SUPABASE_API_KEY:
    # Log de depuração para você saber o que está vazio
    print(f"DEBUG: URL encontrada: {bool(SUPABASE_URL)}")
    print(f"DEBUG: KEY encontrada: {bool(SUPABASE_API_KEY)}")
    raise RuntimeError('Erro: As chaves do Supabase não foram encontradas no .env. Verifique os nomes das variáveis.')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_API_KEY)

def get_supabase_client() -> Client:
    return supabase

def insert_leitura_supabase(id_qrcode, valor, tipo_registro="MISTO", leiturista="Zelador"):
    """Insere leitura usando o nome de coluna exato: id"""
    try:
        leituras_obj = {
            "id": str(id_qrcode),             # <-- Nome exato da coluna no seu Supabase
            "valor_leitura": float(valor),    # <-- Nome da coluna de valor
            "tipo_registro": tipo_registro,
            "leiturista": leiturista
        }

        # O on_conflict deve ser 'id' pois é a sua chave primária/única na tabela
        result = supabase.table('leituras').upsert(
            leituras_obj, on_conflict='id' 
        ).execute()

        return {'sucesso': True, 'mensagem': 'Sincronizado!', 'data': result.data}

    except Exception as e:
        return {'sucesso': False, 'mensagem': f'❌ Erro: {e}'}