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
            cursor = conn.cursor()
            
            # 1. Busca tudo que está na fila com status PENDENTE
            cursor.execute("""
                SELECT q.id, q.leitura_id, l.unidade, l.leitura_atual, l.data_leitura, l.tipo 
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
                
                # Prepara o objeto para o Supabase (deve bater com as colunas da sua tabela remota)
                payload = {
                    "unidade": unidade,
                    "leitura_atual": valor,
                    "data_leitura": data,
                    "tipo": tipo,
                    "condominio": "Vivere Prudente"
                }

                print(f"📡 Enviando Unidade {unidade}...")
                
                # 2. Chama o seu método do supabase_client
                resultado = insert_leitura_supabase(payload)

                if resultado['sucesso']:
                    # 3. Se deu certo, atualiza o status na fila e na tabela principal
                    cursor.execute("UPDATE sync_queue SET status_envio = 'CONCLUIDO' WHERE id = ?", (sync_id,))
                    cursor.execute("UPDATE leituras SET sincronizado = 1 WHERE id = ?", (leitura_id,))
                    print(f"✔️ Unidade {unidade} sincronizada com sucesso!")
                else:
                    print(f"❌ Falha ao sincronizar {unidade}: {resultado['mensagem']}")

            conn.commit()

# Exemplo de como você chamará isso no main.py ou em um botão:
# SyncService.processar_fila()