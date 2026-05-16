"""
Popula as tabelas 'unidades' e 'medidores' no Supabase com todas as
unidades do condomínio. Deve ser executado uma única vez na configuração
inicial ou quando novas unidades forem adicionadas.

Uso: python utils/seed_supabase.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import Database
from supabase import create_client


def seed_unidades_e_medidores():
    if not Database.url or not Database.key_admin:
        print("[ERRO] SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY nao configurados no .env")
        return False

    sb = create_client(Database.url, Database.key_admin)
    unidades = Database._gerar_lista_unidades()

    existing_u = {r['id_qrcode'] for r in sb.table('unidades').select('id_qrcode').execute().data}
    existing_m = {r['id_qrcode'] for r in sb.table('medidores').select('id_qrcode').execute().data}

    novos_u = [{'id_qrcode': u, 'descricao': u, 'bloco': 'VIVERE'}
               for u in unidades if u not in existing_u]

    novos_m = [{'id_qrcode': u, 'unidade_id': u}
               for u in unidades if u not in existing_m]

    if novos_u:
        sb.table('unidades').insert(novos_u).execute()
        print(f"[OK] Inseridas {len(novos_u)} unidades novas")
    else:
        print("[OK] Tabela 'unidades' ja esta completa")

    if novos_m:
        sb.table('medidores').insert(novos_m).execute()
        print(f"[OK] Inseridos {len(novos_m)} medidores novos")
    else:
        print("[OK] Tabela 'medidores' ja esta completa")

    total_u = len(sb.table('unidades').select('id_qrcode').execute().data)
    total_m = len(sb.table('medidores').select('id_qrcode').execute().data)
    print(f"Total final: {total_u} unidades | {total_m} medidores no Supabase")
    return True


if __name__ == "__main__":
    seed_unidades_e_medidores()
