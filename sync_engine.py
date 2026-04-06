from database.database import Database
from database.supabase_client import get_supabase_client


class SyncEngine:
    @classmethod
    def sincronizar_tudo(cls, som_sucesso=None):
        """
        Sincroniza leituras pendentes com o Supabase e dispara feedback sonoro.
        """
        cliente = get_supabase_client()
        if not cliente:
            return "❌ Erro: Nuvem não configurada"

        with Database.get_db() as conn:
            cursor = conn.cursor()
            # Busca apenas o que não foi enviado ainda
            cursor.execute("SELECT * FROM leituras WHERE sincronizado = 0")
            pendentes = cursor.fetchall()

            if not pendentes:
                return "✅ Tudo em dia!"

            sucessos = 0
            for row in pendentes:
                try:
                    # Envio para o Supabase usando o mapeamento correto
                    cliente.table("leituras").insert({
                        "valor_leitura": row['valor'],
                        "tipo_registro": row['tipo_leitura'],
                        "data_hora_coleta": row['data_leitura'],
                        "leiturista": "Zelador"
                    }).execute()

                    # Atualiza o status local para evitar reenvio
                    cursor.execute(
                        "UPDATE leituras SET sincronizado = 1 WHERE id = ?", (row['id'],))
                    conn.commit()
                    sucessos += 1
                except Exception as e:
                    print(f"Erro ao sincronizar ID {row['id']}: {e}")
                    continue

            # Feedback de Sucesso com Áudio
            if sucessos > 0:
                if som_sucesso:
                    som_sucesso.play()  # Toca o áudio de sucesso definido
                return f"🚀 {sucessos} registros enviados!"

            return "⚠️ Falha na conexão com a nuvem"

    @classmethod
    def sincronizar_agora(cls, page):
        return cls.sincronizar_tudo()
