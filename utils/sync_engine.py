from database.database import Database
from database.supabase_client import get_supabase_client
import os

class SyncEngine:
    @classmethod
    def sincronizar_tudo(cls, som_sucesso=None):
        cliente = get_supabase_client()
        if not cliente:
            return "❌ Erro: Supabase não conectado"

        try:
            with Database.get_db() as conn:
                cursor = conn.cursor()
                # Coluna leitura_atual conforme seu esquema
                cursor.execute("SELECT id, unidade, leitura_atual, tipo_leitura, data_leitura FROM leituras WHERE sincronizado = 0")
                pendentes = cursor.fetchall()

                if not pendentes: return "✅ Tudo em dia!"

                sucessos = 0
                for row in pendentes:
                    cliente.table("leituras").insert({
                        "unidade_id": row['unidade'],
                        "valor_leitura": row['leitura_atual'],
                        "tipo_registro": row['tipo_leitura'],
                        "data_hora_coleta": row['data_leitura']
                    }).execute()
                    cursor.execute("UPDATE leituras SET sincronizado = 1 WHERE id = ?", (row['id'],))
                    conn.commit()
                    sucessos += 1
                return f"🚀 {sucessos} registros enviados!"
        except Exception as e:
            return f"❌ Erro: {e}"

    @classmethod
    def sincronizar_agora(cls, page=None):
        return cls.sincronizar_tudo()