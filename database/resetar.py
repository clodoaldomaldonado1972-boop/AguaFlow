import database as db

def forcar_reset():
    conn = None
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE leituras SET leitura_atual = NULL, status = 'PENDENTE'")
        conn.commit()
        conn.close()
        conn = None
        print("✅ BANCO RESETADO! Agora tente abrir o Iniciar Medição.")
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ ERRO: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    forcar_reset()