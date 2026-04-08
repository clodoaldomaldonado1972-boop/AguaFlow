import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# --- AJUSTE DE CAMINHO DO AMBIENTE ---
# Como este arquivo está em database/, subimos um nível para achar o .env na raiz
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Nomes das variáveis conforme o seu arquivo .env
SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_API_KEY = os.getenv('NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY')

_supabase_client: Client = None

# Inicialização segura do cliente
if SUPABASE_URL and SUPABASE_API_KEY:
    try:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_API_KEY)
    except Exception as e:
        print(f"⚠️ Supabase indisponível: {e}")
else:
    print("⚠️ Chaves do Supabase não encontradas no .env — modo offline ativo.")


def get_supabase_client():
    """Retorna o cliente Supabase ou None se não configurado."""
    return _supabase_client


def insert_leitura_supabase(id_unidade, valor, tipo_leitura="Água", leiturista="Zelador"):
    """
    Realiza o UPSERT (insere ou atualiza) de uma leitura na nuvem usando o ID da unidade.
    """
    cliente = get_supabase_client()
    if not cliente:
        return {'sucesso': False, 'mensagem': 'Modo offline: Cliente não configurado.'}

    try:
        # Mapeamento de dados conforme a estrutura da sua tabela remota[cite: 17]
        leituras_obj = {
            # Chave única (Apto XXX)[cite: 17]
            "id": str(id_unidade),
            "valor_leitura": float(valor),    # Valor medido[cite: 17]
            "tipo_registro": tipo_leitura,    # Água ou Gás
            "leiturista": leiturista          # Nome do operador
        }

        # O 'upsert' garante que, se você ler o mesmo apartamento duas vezes,
        # a nuvem apenas atualizará o valor anterior[cite: 17].
        result = cliente.table('leituras').upsert(
            leituras_obj, on_conflict='id'
        ).execute()

        return {'sucesso': True, 'mensagem': 'Sincronizado!', 'data': result.data}

    except Exception as e:
        return {'sucesso': False, 'mensagem': f'❌ Erro Supabase: {e}'}
