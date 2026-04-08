from database.database import Database
from database.supabase_client import get_supabase_client
import os
import sys

# AJUSTE DE PATH: Faz o script enxergar a raiz do projeto (C:\AguaFlow)
caminho_raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if caminho_raiz not in sys.path:
    sys.path.append(caminho_raiz)

# Imports corretos após o ajuste de path


class SyncEngine:
    @classmethod
    def sincronizar_tudo(cls, som_sucesso=None):
        """
        Sincroniza leituras pendentes com o Supabase e dispara feedback sonoro.
        """
        cliente = get_supabase_client()
        if not cliente:
            return "❌ Erro: Nuvem não configurada"

        try:
            # Abrimos a conexão com o banco local
            with Database.get_db() as conn:
                cursor = conn.cursor()
                # Busca apenas registros que ainda não foram sincronizados
                cursor.execute("SELECT * FROM leituras WHERE sincronizado = 0")
                pendentes = cursor.fetchall()

                if not pendentes:
                    return "✅ Tudo em dia!"

                sucessos = 0
                for row in pendentes:
                    try:
                        # Envio para o Supabase (mapeamento confirmado pelo seu SELECT SQL)
                        cliente.table("leituras").insert({
                            # Mudamos de _id para unidade_id
                            "unidade_id": row['unidade'],
                            "valor_leitura": row['valor'],
                            "tipo_registro": row['tipo_leitura'],
                            "leiturista": "Zelador",
                            "data_hora_coleta": row['data_leitura']
                        }).execute()

                        # Atualiza o status local para 1 (sincronizado) para evitar reenvio
                        cursor.execute(
                            "UPDATE leituras SET sincronizado = 1 WHERE id = ?",
                            (row['id'],)
                        )
                        conn.commit()
                        sucessos += 1

                    except Exception as e:
                        print(f"Erro ao sincronizar ID {row['id']}: {e}")
                        continue

                # Feedback de Sucesso
                if sucessos > 0:
                    if som_sucesso:
                        som_sucesso.play()
                    return f"🚀 {sucessos} registros enviados!"

                return "⚠️ Falha no envio para a nuvem"

        except Exception as e:
            return f"❌ Erro no banco local: {e}"

    @classmethod
    def sincronizar_agora(cls, page=None):
        """Atalho para ser chamado diretamente de botões no Flet."""
        return cls.sincronizar_tudo()
