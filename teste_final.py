from database.database import Database
from sync_engine import SyncEngine


def testar_sistema_completo():
    print("\n--- 🔍 INICIANDO VARREDURA REAL AGUAFLOW ---")

    # 1. Reinicializa as unidades (Garante os 98 pontos)
    Database.init_db()

    # 2. Limpa leituras de testes anteriores para não acumular
    with Database.get_db() as conn:
        conn.execute("DELETE FROM leituras")
        conn.commit()

    # 3. Busca a lista exata
    with Database.get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM unidades")
        unidades = cursor.fetchall()

    print(f"🚀 Simulando leitura para {len(unidades)} pontos reais...")

    # 4. Grava as leituras separando Água e Gás
    for registro in unidades:
        u_id = registro['id']
        # Se for a unidade de Lazer, marca como GÁS, senão ÁGUA
        tipo = "GÁS" if "Gás" in u_id else "ÁGUA"

        res = Database.registrar_leitura(u_id, "123.45", tipo)
        if not res['sucesso']:
            print(f"❌ Erro na unidade {u_id}: {res.get('mensagem')}")

    print("✅ Todas as leituras locais gravadas com sucesso.")

    # 5. Sincroniza com o Supabase
    SyncEngine.sincronizar_tudo()


if __name__ == "__main__":
    testar_sistema_completo()
