import time
from datetime import datetime as dt
from .database import Database
from .supabase_client import insert_leitura_supabase


class SyncService:
    @classmethod
    def processar_fila(cls):
        """Varre a fila local e tenta enviar para a nuvem."""
        print("🔄 Iniciando ciclo de sincronização...")

        with Database.get_db() as conn:
            [cite: 12]
            cursor = conn.cursor()

            # 1. Busca leituras pendentes cruzando a fila com a tabela de leituras
            # Nota: Certifique-se de que a tabela sync_queue foi criada no seu Database.init_db()
            cursor.execute("""
                SELECT q.id, q.leitura_id, l.unidade, l.valor, l.data_leitura, l.tipo_leitura 
                FROM sync_queue q
                JOIN leituras l ON q.leitura_id = l.id
                WHERE q.status_envio = 'PENDENTE'
            """)
            pendentes = cursor.fetchall()

            if not pendentes:
                print("✅ Nada para sincronizar.")
                return

            for item in pendentes:
                sync_id, leitura_id, unidade, valor, data, tipo = item

                print(f"📡 Enviando Unidade {unidade}...")

                # 2. Chama o método de inserção no Supabase
                # Ajustado para usar os campos que definimos no supabase_client.py
                resultado = insert_leitura_supabase(
                    id_unidade=unidade,
                    valor=valor,
                    tipo_leitura=tipo
                )

                if resultado['sucesso']:
                    # 3. Atualiza o status na fila e marca como sincronizado na tabela principal
                    cursor.execute(
                        "UPDATE sync_queue SET status_envio = 'CONCLUIDO' WHERE id = ?", (sync_id,))
                    cursor.execute(
                        "UPDATE leituras SET sincronizado = 1 WHERE id = ?", (leitura_id,))
                    print(f"✔️ Unidade {unidade} sincronizada com sucesso!")
                else:
                    print(
                        f"❌ Falha ao sincronizar {unidade}: {resultado['mensagem']}")

            conn.commit()

    @classmethod
    def adicionar_a_fila(cls, leitura_id):
        """Adiciona manualmente um ID de leitura para a fila de processamento."""
        with Database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO sync_queue (leitura_id, status_envio) VALUES (?, 'PENDENTE')",
                (leitura_id,)
            )
            conn.commit()
