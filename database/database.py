import os
import sqlite3
from datetime import datetime as dt
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()


class Database:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "aguaflow.db")

    @classmethod
    @contextmanager
    def get_db(cls):
        """Gerencia a conexão SQLite de forma segura."""
        conn = sqlite3.connect(cls.DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @classmethod
    def init_db(cls):
        """Inicializa tabelas, unidades e a fila de sincronização."""
        with cls.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS unidades (id TEXT PRIMARY KEY)")
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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    leitura_id INTEGER,
                    status_envio TEXT DEFAULT 'PENDENTE',
                    FOREIGN KEY(leitura_id) REFERENCES leituras(id)
                )
            """)

            # Popula as 96 unidades (Andares 16 ao 1, Apartamentos 6 ao 1)
            todas_unidades = [f"Apto {a}{f}" for a in range(
                16, 0, -1) for f in range(6, 0, -1)]
            cursor.executemany(
                "INSERT OR IGNORE INTO unidades (id) VALUES (?)",
                [(u,) for u in todas_unidades]
            )
            conn.commit()

    @classmethod
    def registrar_leitura(cls, unidade, valor, tipo_leitura):
        """Salva localmente e agenda sincronização automática."""
        agora = dt.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            valor_limpo = float(str(valor).replace(',', '.'))
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO leituras (unidade, valor, tipo_leitura, data_leitura, sincronizado) VALUES (?, ?, ?, ?, 0)",
                    (unidade, valor_limpo, tipo_leitura, agora)
                )
                leitura_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO sync_queue (leitura_id, status_envio) VALUES (?, 'PENDENTE')",
                    (leitura_id,)
                )
                conn.commit()
                return {'sucesso': True, 'id': leitura_id}
        except Exception as e:
            return {'sucesso': False, 'mensagem': str(e)}

    @classmethod
    def buscar_proximo_pendente(cls, tipo_filtro="Água"):
        """Retorna a próxima unidade pendente seguindo a ordem do prédio."""
        with cls.get_db() as conn:
            cursor = conn.cursor()
            if tipo_filtro == "Ambos":
                query = "SELECT id FROM unidades WHERE (id NOT IN (SELECT unidade FROM leituras WHERE tipo_leitura = 'Água') OR id NOT IN (SELECT unidade FROM leituras WHERE tipo_leitura = 'Gás')) AND id NOT IN ('Lazer Gás', 'Geral Água')"
                cursor.execute(query)
            else:
                query = "SELECT id FROM unidades WHERE id NOT IN (SELECT unidade FROM leituras WHERE tipo_leitura = ?) AND id NOT IN ('Lazer Gás', 'Geral Água')"
                cursor.execute(query, (tipo_filtro,))

            pendentes = [row[0] for row in cursor.fetchall()]
            if not pendentes:
                return None

            # Ordenação: Andares maiores primeiro, final de apto maior primeiro
            def order_vivere(u):
                num_str = u.replace("Apto ", "")
                return (-int(num_str[:-1]), -int(num_str[-1]))

            pendentes.sort(key=order_vivere)
            escolhido = pendentes[0]
            return (escolhido, escolhido, tipo_filtro)

    @classmethod
    def buscar_todas_leituras(cls):
        """Retorna todas as leituras registradas para o dashboard."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT unidade, valor, data_leitura, tipo_leitura FROM leituras ORDER BY data_leitura DESC")
                linhas = cursor.fetchall()
                return [dict(row) for row in linhas]
        except Exception as e:
            print(f"Erro ao buscar todas as leituras: {e}")
            return []

    @classmethod
    def buscar_relatorio_geral(cls):
        """Consolida leituras atuais e anteriores para o relatório PDF."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT unidade, valor, data_leitura FROM leituras ORDER BY unidade, data_leitura DESC")
                linhas = cursor.fetchall()
                relatorio = {}
                for linha in linhas:
                    unidade = linha[0]
                    if unidade not in relatorio:
                        relatorio[unidade] = [linha[1], 0.0, linha[2], ""]
                    elif relatorio[unidade][1] == 0.0:
                        relatorio[unidade][1] = linha[1]
                        relatorio[unidade][3] = linha[2]
                return [(u, v[0], v[1], v[2], v[3]) for u, v in sorted(relatorio.items())]
        except Exception as e:
            print(f"Erro ao buscar relatório: {e}")
            return []
