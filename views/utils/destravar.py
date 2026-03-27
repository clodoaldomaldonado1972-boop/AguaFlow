import sqlite3

def destravar_sistema():
    try:
        # 1. Conecta ao banco local
        # Se o arquivo estiver em views/utils, o caminho do banco volta duas pastas
        conn = sqlite3.connect("aguaflow.db")
        cursor = conn.cursor()

        print("--- 🛠️ MANUTENÇÃO AGUAFLOW ---")

        # 2. Destrava a unidade 166 (Marca como concluída)
        cursor.execute("UPDATE leituras SET status = 'CONCLUIDO' WHERE unidade = '166'")
        
        # 3. Limpa todas as leituras que estão com "restos" decimais (mais de 2 casas)
        # O SQLite arredonda tudo o que já foi salvo para 2 casas
        cursor.execute("UPDATE leituras SET leitura_atual = ROUND(leitura_atual, 2) WHERE leitura_atual IS NOT NULL")

        conn.commit()
        
        if cursor.rowcount > 0:
            print(f"✅ Sucesso! Unidade 166 destravada.")
            print(f"✅ Dados limpos: {cursor.rowcount} registros arredondados.")
        else:
            print("⚠️ Nenhuma pendência encontrada para a unidade 166.")

        conn.close()
    except Exception as e:
        print(f"❌ Erro ao destravar: {e}")

if __name__ == "__main__":
    destravar_sistema()