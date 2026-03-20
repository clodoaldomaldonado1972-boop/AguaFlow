import database as db

def forcar_reset():
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        # Limpa as leituras para o sistema entender que há trabalho a fazer
        cursor.execute("UPDATE leituras SET leitura_atual = NULL")
        conn.commit()
        print("✅ BANCO RESETADO! Agora tente abrir o Iniciar Medição.")
    except Exception as e:
        print(f"❌ ERRO: {e}")

if __name__ == "__main__":
    forcar_reset()