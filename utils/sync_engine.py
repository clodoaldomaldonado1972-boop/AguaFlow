from database.database import Database
# Import corrigido para buscar o cliente dentro da pasta database
from database.supabase_client import get_supabase_client[cite: 16]


class SyncEngine:
    @classmethod
    def sincronizar_tudo(cls, som_sucesso=None):
        """
        Sincroniza leituras pendentes com o Supabase e dispara feedback sonoro.
        """
        cliente = get_supabase_client()[cite: 16]
        if not cliente:
            return "❌ Erro: Nuvem não configurada"[cite: 16]

        with Database.get_db() as conn:
            [cite: 12, 16]
            cursor = conn.cursor()
            # Busca apenas registros que ainda não foram sincronizados (sincronizado = 0)[cite: 16]
            cursor.execute("SELECT * FROM leituras WHERE sincronizado = 0")
            pendentes = cursor.fetchall()[cite: 16]

            if not pendentes:
                return "✅ Tudo em dia!"[cite: 16]

            sucessos = 0
            for row in pendentes:
                try:
                    # Envio para o Supabase usando o mapeamento de campos da tabela remota[cite: 16]
                    cliente.table("leituras").insert({
                        # Adicionado para identificar o apartamento na nuvem
                        "unidade": row['unidade'],
                        "valor_leitura": row['valor'],
                        "tipo_registro": row['tipo_leitura'],
                        "data_hora_coleta": row['data_leitura'],
                        "leiturista": "Zelador"
                    }).execute()[cite: 16]

                    # Atualiza o status local para 1 (sincronizado) para evitar reenvio[cite: 16]
                    cursor.execute(
                        "UPDATE leituras SET sincronizado = 1 WHERE id = ?", (row['id'],))
                    conn.commit()[cite: 16]
                    sucessos += 1
                except Exception as e:
                    print(f"Erro ao sincronizar ID {row['id']}: {e}")
                    continue [cite: 16]

            # Feedback de Sucesso com Áudio (se configurado na View)[cite: 16]
            if sucessos > 0:
                if som_sucesso:
                    som_sucesso.play()
                return f"🚀 {sucessos} registros enviados!"[cite: 16]

            return "⚠️ Falha na conexão com a nuvem"[cite: 16]

    @classmethod
    def sincronizar_agora(cls, page):
        """Atalho para ser chamado diretamente de botões no Flet[cite: 16]."""
        return cls.sincronizar_tudo()[cite: 16]
