from database.database import Database
from database.supabase_client import insert_leitura_supabase
from datetime import datetime

class SyncEngine:
    @classmethod
    def sincronizar_tudo(cls):
        """Lê todas as leituras concluídas no SQLite e envia para o Supabase."""
        print("🚀 Iniciando sincronização total com o Supabase...")
        
        # Busca apenas unidades que já foram medidas
        with Database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT unidade, leitura_atual, tipo, status FROM leituras WHERE status = 'CONCLUIDO'")
            leituras_locais = cursor.fetchall()

        if not leituras_locais:
            print("pnd Nada concluído localmente para sincronizar.")
            return

        sucessos = 0
        erros = 0

        for unidade, valor, tipo, status in leituras_locais:
            # O '_id' no seu Supabase conecta com o 'id_qrcode' da tabela unidades
            # Valor deve ser o número capturado pelo zelador
            resultado = insert_leitura_supabase(
                id_qrcode=unidade, 
                valor=valor, 
                tipo_registro=tipo
            )

            if resultado['sucesso']:
                sucessos += 1
                # Marca como sincronizado no SQLite para evitar reenvio desnecessário
                with Database.get_db() as conn:
                    conn.cursor().execute("UPDATE leituras SET sincronizado = 1 WHERE unidade = ?", (unidade,))
                    conn.commit()
            else:
                erros += 1
                print(f"❌ Erro na unidade {unidade}: {resultado['mensagem']}")

        print(f"\n✅ Sincronização finalizada!")
        print(f"📊 Sucessos: {sucessos} | Falhas: {erros}")

# Para rodar agora, você pode chamar no terminal:
# python -c "from database.sync_engine import SyncEngine; SyncEngine.sincronizar_tudo()"