from database.database import Database
from database.supabase_client import get_supabase_client
import os
import sys

# AJUSTE DE PATH
caminho_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if caminho_raiz not in sys.path:
    sys.path.append(caminho_raiz)

class SyncEngine:
    @classmethod
    def sincronizar_tudo(cls, som_sucesso=None):
        cliente = get_supabase_client()
        if not cliente:
            return "❌ Erro: Nuvem não configurada"

        try:
            with Database.get_db() as conn:
                cursor = conn.cursor()
                # Busca registros pendentes usando a coluna leitura_atual
                cursor.execute("SELECT id, unidade, leitura_atual, tipo_leitura, data_leitura FROM leituras WHERE sincronizado = 0")
                pendentes = cursor.fetchall()

                if not pendentes:
                    return "✅ Tudo em dia!"

                sucessos = 0
                for row in pendentes:
                    try:
                        cliente.table("leituras").insert({
                            "unidade_id": row['unidade'],
                            "valor_leitura": row['leitura_atual'], # Mapeamento correto
                            "tipo_registro": row['tipo_leitura'],
                            "leiturista": "Zelador",
                            "data_hora_coleta": row['data_leitura']
                        }).execute()

                        cursor.execute("UPDATE leituras SET sincronizado = 1 WHERE id = ?", (row['id'],))
                        conn.commit()
                        sucessos += 1
                    except Exception as e:
                        print(f"Erro ao sincronizar ID {row['id']}: {e}")
                        continue

                if sucessos > 0:
                    if som_sucesso: som_sucesso.play()
                    return f"🚀 {sucessos} registros enviados!"
                return "⚠️ Falha no envio para a nuvem"
        except Exception as e:
            return f"❌ Erro no banco local: {e}"

    @classmethod
    def sincronizar_agora(cls, page=None):
        return cls.sincronizar_tudo()