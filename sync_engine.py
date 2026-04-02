from database.database import Database


class SyncEngine:
    @classmethod
    def sincronizar_tudo(cls):
        if not Database.supabase:
            print("❌ Erro: Cliente Supabase não inicializado.")
            return

        print("\n🚀 Iniciando motor de sincronização...")

        with Database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM leituras WHERE sincronizado = 0")
            pendentes = cursor.fetchall()

            if not pendentes:
                print("✅ Tudo em dia! Nenhuma leitura pendente.")
                return

            print(f"📊 Sincronizando {len(pendentes)} registro(s)...")

            for row in pendentes:
                try:
                    # Envio efetivo para a nuvem com mapeamento correto
                    Database.supabase.table("leituras").insert({
                        "valor_leitura": row['valor'],
                        "tipo_registro": row['tipo_leitura'],
                        "data_hora_coleta": row['data_leitura'],
                        "leiturista": "Zelador"
                    }).execute()

                    # Marca como sincronizado localmente apenas se o insert acima funcionar
                    cursor.execute(
                        "UPDATE leituras SET sincronizado = 1 WHERE id = ?", (row['id'],))
                    conn.commit()
                    print(f"✔️ Unidade {row['unidade']} sincronizada!")
                except Exception as e:
                    print(f"❌ Erro na Unidade {row['unidade']}: {e}")
