import os
import sqlite3
import csv
import logging
from datetime import datetime as dt
from contextlib import contextmanager
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
logging.getLogger("httpx").setLevel(logging.ERROR)

class Database:
    url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY") or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    supabase = None

    try:
        if url and key:
            supabase = create_client(url, key)
            print("🌐 Supabase conectado com sucesso!")
    except Exception as e:
        print(f"⚠️ Modo Offline: Supabase indisponível ({e})")

    @classmethod
    @contextmanager
    def get_db(cls):
        """Gerencia conexão para evitar travamentos."""
        conn = sqlite3.connect("aguaflow.db", check_same_thread=False)
        try:
            yield conn
        finally:
            conn.close()

    @classmethod
    def init_db(cls):
        """Inicializa o banco e gera as 98 unidades do Vivere Prudente."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS leituras (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        unidade TEXT NOT NULL,
                        leitura_atual REAL,
                        status TEXT DEFAULT 'PENDENTE',
                        data_leitura TEXT,
                        tipo TEXT DEFAULT 'MISTO',
                        sincronizado INTEGER DEFAULT 0
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sync_queue (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        leitura_id INTEGER,
                        data_tentativa TEXT,
                        status_envio TEXT DEFAULT 'PENDENTE',
                        FOREIGN KEY (leitura_id) REFERENCES leituras (id)
                    )
                """)
                cursor.execute("SELECT COUNT(*) FROM leituras")
                if cursor.fetchone()[0] == 0:
                    print("📦 Gerando lista Vivere Prudente...")
                    unidades = []
                    for andar in range(16, 0, -1):
                        for apto in range(6, 0, -1):
                            unidades.append((f"{andar}{apto}", 'MISTO'))
                    unidades.append(("LAZER", "GAS_SOMENTE"))
                    unidades.append(("GERAL", "AGUA_SOMENTE"))
                    cursor.executemany("INSERT INTO leituras (unidade, tipo) VALUES (?, ?)", unidades)
                conn.commit()
            print("✅ Banco de dados pronto.")
        except Exception as e:
            print(f"❌ Erro ao inicializar banco: {e}")

    @staticmethod
    def limpar_valor_leitura(valor_str):
        """Transforma '123,456' em 123.456 e remove caracteres estranhos."""
        if not valor_str: return 0.0
        s = str(valor_str).replace(',', '.')
        valor_limpo = "".join(c for c in s if c.isdigit() or c == '.')
        try:
            return float(valor_limpo)
        except ValueError:
            return 0.0

    @classmethod
    def validar_valor(cls, valor_str):
        """Barreira para aceitar vírgula/ponto e manter as 7 casas decimais."""
        if not valor_str: 
            return {'valido': False, 'mensagem': '❌ Campo vazio'}
        
        v = cls.limpar_valor_leitura(valor_str)
        
        if 0 <= v <= 9999999.9999999: 
            return {'valido': True, 'valor': round(v, 7)} 
        return {'valido': False, 'mensagem': '❌ Valor fora do limite (Máx 7 dígitos)'}

    @classmethod
    def buscar_proximo_pendente(cls):
        with cls.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, unidade, tipo FROM leituras WHERE status = 'PENDENTE' ORDER BY id ASC LIMIT 1")
            return cursor.fetchone()

    @classmethod
    def registrar_leitura(cls, id_db, valor):
        validacao = cls.validar_valor(valor)
        if not validacao['valido']: 
            return {'sucesso': False, 'mensagem': validacao['mensagem']}

        with cls.get_db() as conn:
            try:
                cursor = conn.cursor()
                agora = dt.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("""
                    UPDATE leituras 
                    SET leitura_atual = ?, status = 'CONCLUIDO', data_leitura = ?, sincronizado = 0
                    WHERE id = ?
                """, (validacao['valor'], agora, id_db))
                cursor.execute("""
                    INSERT INTO sync_queue (leitura_id, data_tentativa, status_envio)
                    VALUES (?, ?, 'PENDENTE')
                """, (id_db, agora))
                conn.commit()
                return {'sucesso': True, 'mensagem': "✅ Salvo e pronto para sincronizar!"}
            except Exception as e:
                conn.rollback()
                return {'sucesso': False, 'mensagem': f"Erro ao gravar: {e}"}

    @classmethod
    def processar_fila(cls):
        """Auto-Sync para o Supabase."""
        if not cls.supabase: return
        with cls.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, unidade, leitura_atual FROM leituras WHERE status = 'CONCLUIDO' AND sincronizado = 0")
            for id_db, uni, val in cursor.fetchall():
                try:
                    cls.supabase.table("leituras").insert({"unidade_id": uni, "valor": val}).execute()
                    cursor.execute("UPDATE leituras SET sincronizado = 1 WHERE id = ?", (id_db,))
                    conn.commit()
                except: continue

    @classmethod
    def exportar_csv(cls):
        with cls.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT unidade, leitura_atual, data_leitura FROM leituras WHERE status = 'CONCLUIDO' ORDER BY id ASC")
            dados = cursor.fetchall()
            if not dados: return False
            try:
                if not os.path.exists("relatorios"): os.makedirs("relatorios")
                caminho = f"relatorios/leitura_vivere_{dt.now().strftime('%Y%m%d_%H%M')}.csv"
                with open(caminho, "w", newline="", encoding="utf-8-sig") as f:
                    escritor = csv.writer(f, delimiter=';')
                    escritor.writerow(["Unidade", "Leitura", "Data"])
                    escritor.writerows(dados)
                return True
            except: return False