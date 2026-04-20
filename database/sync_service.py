import time
import asyncio
from datetime import datetime as dt
from .database import Database

class SyncService:
    @classmethod
    async def processar_fila(cls):
        """
        Varre o SQLite local em busca de leituras não sincronizadas 
        e tenta enviá-las para o Supabase (Nuvem).
        """
        print("🔄 AguaFlow: Iniciando ciclo de sincronização...")

        # 1. Busca no Banco Local apenas o que ainda não subiu para a nuvem (sincronizado = 0)
        # IHC: Isso evita consumo desnecessário de dados móveis do zelador.
        with Database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, unidade, leitura_atual, consumo, tipo_leitura, data_hora_coleta 
                FROM leituras 
                WHERE sincronizado = 0
            """)
            pendentes = cursor.fetchall()

            if not pendentes:
                print("✅ Tudo em dia: Nada para sincronizar.")
                return 0

            sucessos = 0
            for item in pendentes:
                leitura_id = item['id']
                unidade = item['unidade']
                
                print(f"📡 Enviando Unidade {unidade} para a nuvem...")

                # 2. Tenta enviar para o Supabase usando o método que criamos no Database
                # O Database.sincronizar_com_supabase já trata a conexão com a nuvem
                resultado_ok = await cls._enviar_para_nuvem(item)

                if resultado_ok:
                    # 3. Se subiu com sucesso, marca como sincronizado no SQLite local
                    cursor.execute(
                        "UPDATE leituras SET sincronizado = 1 WHERE id = ?", (leitura_id,)
                    )
                    sucessos += 1
                    print(f"✔️ Unidade {unidade} sincronizada com sucesso!")
                else:
                    print(f"❌ Falha temporária ao sincronizar {unidade}. Tentará novamente depois.")

            conn.commit()
            return sucessos

    @classmethod
    async def _enviar_para_nuvem(cls, dados_leitura):
        """
        Função interna que faz a ponte real com o Supabase.
        Retorna True se a nuvem confirmou o recebimento.
        """
        try:
            # Reutiliza a lógica central de sincronismo do seu Database.py
            # Isso mantém o código limpo e evita repetição de chaves de API
            registros_enviados = Database.sincronizar_com_supabase()
            return registros_enviados > 0
        except Exception as e:
            print(f"⚠️ Erro de rede no envio: {e}")
            return False

    @classmethod
    def adicionar_a_fila(cls, leitura_id):
        """
        Método de apoio para marcar manualmente uma leitura para re-envio se necessário.
        """
        with Database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE leituras SET sincronizado = 0 WHERE id = ?", (leitura_id,)
            )
            conn.commit()