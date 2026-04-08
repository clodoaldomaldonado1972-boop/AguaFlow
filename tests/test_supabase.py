from database.supabase_client import get_supabase_client


def main():
    supabase = get_supabase_client()

    try:
        result = supabase.table('unidades').select('*').limit(5).execute()

        if hasattr(result, 'error') and result.error:
            print('Erro Supabase:', result.error)
            return

        data = getattr(result, 'data', None)
        if not data:
            print('Conexão OK, mas tabela "unidades" está vazia')
            return

        print('Primeiras 5 linhas da tabela unidades:')
        for idx, row in enumerate(data, start=1):
            print(idx, row)

    except Exception as e:
        print('Falha ao testar Supabase:', e)


if __name__ == '__main__':
    main()
