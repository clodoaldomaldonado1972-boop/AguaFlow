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
        """Gerencia conexão para evitar travamentos (Database is locked)."""
        conn = sqlite3.connect("aguaflow.db", check_same_thread=False)
        try:
            yield conn
        finally:
            conn.close()

    @classmethod
    def init_db(cls):
        """Inicializa o banco, gera as 98 unidades e cria a fila de sincronização."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                
                # 1. Tabela de Leituras (Cofre Local)
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

                # 2. Tabela de Fila de Sincronização (Motor de Sync - Seção 2.3)
                # Esta tabela garante que nenhuma leitura se perca se o sinal cair
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sync_queue (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        leitura_id INTEGER,
                        data_tentativa TEXT,
                        status_envio TEXT DEFAULT 'PENDENTE',
                        FOREIGN KEY (leitura_id) REFERENCES leituras (id)
                    )
                """)
                
                # 3. Populando as unidades (16 andares x 6 aptos + 2 áreas comuns)
                cursor.execute("SELECT COUNT(*) FROM leituras")
                if cursor.fetchone()[0] == 0:
                    print("📦 Gerando lista Vivere Prudente (16º ao 1º)...")
                    unidades = []
                    # Gerar do 166 ao 11
                    for andar in range(16, 0, -1):
                        for apto in range(6, 0, -1):
                            unidades.append((f"{andar}{apto}", 'MISTO'))
                    
                    # Áreas comuns
                    unidades.append(("LAZER", "GAS_SOMENTE"))
                    unidades.append(("GERAL", "AGUA_SOMENTE"))
                    
                    cursor.executemany(
                        "INSERT INTO leituras (unidade, tipo) VALUES (?, ?)", 
                        unidades
                    )
                
                conn.commit()
            print("✅ Banco de dados e Fila de Sync prontos.")
            
        except Exception as e:
            print(f"❌ Erro ao inicializar banco (Seção 1.7): {e}")

    @classmethod
    def validar_valor(cls, valor_str):
        """Barreira dos 7 dígitos (Ex: 00000,00)."""
        if not valor_str: return {'valido': False, 'mensagem': '❌ Campo vazio'}
        valor_limpo = str(valor_str).replace(',', '.')
        try:
            v = float(valor_limpo)
            if 0 <= v <= 99999.99:
                return {'valido': True, 'valor': round(v, 2)}
            return {'valido': False, 'mensagem': '❌ Máximo 7 dígitos (99999,99)'}
        except: return {'valido': False, 'mensagem': '❌ Valor inválido'}

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
                
                # 1. Atualiza a leitura local
                # Note: sincronizado = 0 garante que o app saiba que este dado é novo
                cursor.execute("""
                    UPDATE leituras 
                    SET leitura_atual = ?, status = 'CONCLUIDO', data_leitura = ?, sincronizado = 0
                    WHERE id = ?
                """, (validacao['valor'], agora, id_db))

                # 2. Alimenta a Fila de Sincronização (Seção 2.3)
                # O motor de sync vai olhar para esta tabela depois
                cursor.execute("""
                    INSERT INTO sync_queue (leitura_id, data_tentativa, status_envio)
                    VALUES (?, ?, 'PENDENTE')
                """, (id_db, agora))

                conn.commit()
                return {'sucesso': True, 'mensagem': "✅ Salvo e pronto para sincronizar!"}
            
            except Exception as e:
                conn.rollback() # Segurança total contra corrupção de dados
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