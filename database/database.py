import os
import sqlite3
from datetime import datetime as dt
from contextlib import contextmanager
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()


class Database:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "aguaflow.db")

    # Usa as chaves exatamente como estão no seu .env
    url = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    key = os.environ.get("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY")
    supabase = None

    if url and key:
        try:
            supabase = create_client(url, key)
        except Exception as e:
            print(f"⚠️ Erro ao conectar: {e}")

    @classmethod
    @contextmanager
    def get_db(cls):
        conn = sqlite3.connect(cls.DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @classmethod
    def init_db(cls):
        """Inicializa tabelas e limpa unidades antigas para usar a contagem correta."""
        with cls.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leituras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unidade TEXT,
                    valor REAL,
                    tipo_leitura TEXT,
                    data_leitura TEXT,
                    sincronizado INTEGER DEFAULT 0
                )
            """)
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS unidades (id TEXT PRIMARY KEY)")

            # Limpa e recria as unidades para garantir que sejam apenas as 98 corretas
            cursor.execute("DELETE FROM unidades")

            # 96 Apartamentos (Exemplo: do 11 ao 166, totalizando 96 se considerar os saltos de andares)
            # Para o teste, vamos gerar exatamente 96 IDs de apartamentos
            aps = [f"Apto {u}" for u in range(1, 97)]
            especiais = ["Lazer Gás", "Geral Água"]
            todas = aps + especiais

            cursor.executemany("INSERT INTO unidades (id) VALUES (?)", [
                               (u,) for u in todas])
            conn.commit()
            print(f"✅ Tabelas prontas. Unidades carregadas: {len(todas)}")

    @classmethod
    def registrar_leitura(cls, unidade, valor, tipo_leitura):
        """ESTA É A FUNÇÃO QUE ESTAVA FALTANDO"""
        agora = dt.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            # Limpeza simples do valor
            valor_limpo = float(str(valor).replace(',', '.'))
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO leituras (unidade, valor, tipo_leitura, data_leitura, sincronizado)
                    VALUES (?, ?, ?, ?, 0)
                """, (unidade, valor_limpo, tipo_leitura, agora))
                conn.commit()
                return {'sucesso': True}
        except Exception as e:
            return {'sucesso': False, 'mensagem': str(e)}
