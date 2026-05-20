import os
import sqlite3
import csv
import logging
import traceback
from contextlib import contextmanager
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Caminho explícito para achar .env tanto no desktop quanto no Android
_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '.env')
load_dotenv(_ENV_PATH, override=False)
load_dotenv(override=False)  # fallback: cwd e variáveis de ambiente do sistema

# Utiliza o logger configurado centralmente
logger = logging.getLogger(__name__)


class Database:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "aguaflow.db")

    # --- INICIALIZAÇÃO DO SUPABASE ---
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    key_admin = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    # Definimos explicitamente como None para evitar AttributeError em outros arquivos
    supabase: Client = None
    supabase_admin: Client = None

    if url and key:
        try:
            supabase = create_client(url, key)
            logger.info("✅ Conexão com Supabase estabelecida.")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao Supabase: {e}")

    if url and key_admin:
        try:
            supabase_admin = create_client(url, key_admin)
            logger.info("✅ Conexão Admin com Supabase estabelecida.")
        except Exception as e:
            logger.error(f"❌ Erro ao conectar ao Supabase Admin: {e}")

    @classmethod
    @contextmanager
    def get_db(cls):
        """Abre a conexão garantindo o fechamento seguro."""
        os.makedirs(os.path.dirname(cls.DB_PATH), exist_ok=True)
        conn = sqlite3.connect(
            cls.DB_PATH, check_same_thread=False, timeout=20)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    @classmethod
    def inicializar_tabelas(cls):
        """Cria a estrutura e realiza migrações de colunas necessárias para o Vivere."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()

                # 1. Cria a tabela base com os campos fundamentais
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS leituras (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        unidade_id TEXT NOT NULL,
                        tipo TEXT NOT NULL,
                        sincronizado INTEGER DEFAULT 0
                    )
                """)

                # 2. Migrações Individuais: Garante compatibilidade total com o Supabase
                # Lista atualizada com os nomes de colunas que vimos no seu esquema visual
                migracoes = [
                    # Adiciona a coluna data_hora_coleta se não existir
                    "ALTER TABLE leituras ADD COLUMN data_hora_coleta TEXT",
                    # Adiciona a coluna valor_leitura se não existir (para compatibilidade)
                    "ALTER TABLE leituras ADD COLUMN valor_leitura REAL",
                    # Adiciona a coluna leitura_agua se não existir
                    "ALTER TABLE leituras ADD COLUMN leitura_agua REAL",
                    # Adiciona a coluna leitura_gas se não existir
                    "ALTER TABLE leituras ADD COLUMN leitura_gas REAL",
                    # Adiciona a coluna tipo_registro se não existir
                    "ALTER TABLE leituras ADD COLUMN tipo_registro TEXT",
                    # Adiciona a coluna leiturista se não existir
                    "ALTER TABLE leituras ADD COLUMN leiturista TEXT",
                    "ALTER TABLE leituras ADD COLUMN foto_url TEXT",
                    "ALTER TABLE leituras ADD COLUMN consumo REAL",
                    "ALTER TABLE leituras ADD COLUMN path_foto TEXT"  # Crucial para o SyncService
                ]

                for comando in migracoes:
                    try:
                        cursor.execute(comando)
                    except Exception:
                        # Se der erro (ex: sqlite3.OperationalError), a coluna já existe
                        pass

                # 3. Tabela de referência — guarda a última leitura de cada ciclo
                #    para exibir "Leitura Anterior" no próximo ciclo
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS leituras_referencia (
                        unidade_id TEXT PRIMARY KEY,
                        leitura_agua REAL,
                        leitura_gas REAL,
                        data_referencia TEXT
                    )
                """)

                # 4. Cria a tabela de usuários se não existir para suporte offline
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nome TEXT NOT NULL,
                        email TEXT UNIQUE NOT NULL,
                        senha TEXT NOT NULL,
                        role TEXT DEFAULT 'user',
                        sincronizado INTEGER DEFAULT 0,
                        criado_em TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)

                # Migração: Garante a coluna sincronizado para usuários offline se a tabela já existia
                try:
                    cursor.execute(
                        "ALTER TABLE usuarios ADD COLUMN sincronizado INTEGER DEFAULT 0")
                except:
                    pass

                # 5. Tracking de versão do schema (migrações versionadas)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INTEGER NOT NULL,
                        aplicado_em TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                v_atual = cursor.execute(
                    "SELECT COALESCE(MAX(version), 0) FROM schema_version"
                ).fetchone()[0]
                if v_atual == 0:
                    cursor.execute("INSERT INTO schema_version (version) VALUES (1)")

                conn.commit()
                logger.info(
                    "🚀 Estrutura do banco de dados (SQLite) sincronizada.")
        except Exception as e:
            logger.critical(
                f"❌ FALHA CRÍTICA NA INICIALIZAÇÃO DO SQLITE: {str(e)}", exc_info=True)
            # Gatilho de E-mail para falha no Boot
            from utils.logger_config import enviar_report_erro
            enviar_report_erro(traceback.format_exc(), unidade="BOOT SYSTEM")
            raise e

    @classmethod
    def criar_usuario(cls, nome, email, senha, role='user'):
        """Cadastra um novo usuário no banco local para suporte ao acesso offline."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO usuarios (nome, email, senha, role)
                    VALUES (?, ?, ?, ?)
                """, (nome, email, senha, role))
                conn.commit()
                logger.info(f"👤 Usuário criado com sucesso no SQLite: {email}")
                return True
        except sqlite3.IntegrityError:
            logger.warning(
                f"⚠️ Tentativa de criar usuário com e-mail já existente: {email}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao criar usuário no SQLite: {e}")
            return False

    @classmethod
    def validar_login_offline(cls, email, senha):
        """Verifica as credenciais no banco local para permitir acesso offline."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, nome, email, role FROM usuarios WHERE email = ? AND senha = ?",
                    (email, senha)
                )
                usuario = cursor.fetchone()
                if usuario:
                    logger.info(f"✅ Login offline realizado: {email}")
                    return dict(usuario)
                return None
        except Exception as e:
            logger.error(f"❌ Erro na validação offline: {e}")
            return None

    @classmethod
    def atualizar_senha(cls, email, nova_senha):
        """Atualiza a senha do usuário no banco local."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE usuarios SET senha = ? WHERE email = ?",
                    (nova_senha, email)
                )
                conn.commit()
                if cursor.rowcount > 0:
                    logger.info(f"🔑 Senha atualizada no SQLite para: {email}")
                    return True
                return False
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar senha no SQLite: {e}")
            return False

    @classmethod
    def deletar_usuario_local(cls, email):
        """Deleta um usuário do banco de dados local."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM usuarios WHERE email = ?", (email,))
                conn.commit()
                if cursor.rowcount > 0:
                    logger.info(f"🗑️ Usuário deletado do SQLite: {email}")
                    return True
                return False
        except Exception as e:
            logger.error(f"❌ Erro ao deletar usuário do SQLite: {e}")
            return False

    @classmethod
    def email_existe(cls, email):
        """Verifica se um e-mail já está cadastrado na tabela de usuários local."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT COUNT(*) FROM usuarios WHERE email = ?", (email,))
                return cursor.fetchone()[0] > 0
        except Exception as e:
            logger.error(
                f"❌ Erro ao verificar existência de e-mail no SQLite: {e}")
            return False

    @classmethod
    def listar_usuarios(cls):
        """Retorna uma lista de todos os usuários cadastrados no SQLite local."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, nome, email, role, sincronizado, criado_em FROM usuarios ORDER BY nome ASC")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"❌ Erro ao listar usuários no SQLite: {e}")
            return []

    @classmethod
    def atualizar_role_usuario(cls, email, nova_role):
        """Atualiza o cargo (role) de um usuário no banco local."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                # Ao alterar a role, marcamos como não sincronizado até que o processo de rede confirme
                cursor.execute(
                    "UPDATE usuarios SET role = ?, sincronizado = 0 WHERE email = ?",
                    (nova_role, email)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar role no SQLite: {e}")
            return False

    @classmethod
    def marcar_usuario_sincronizado(cls, email):
        """Define o status de sincronização do usuário como 1 (Ok)."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE usuarios SET sincronizado = 1 WHERE email = ?", (email,))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"❌ Erro ao marcar sync do usuário: {e}")
            return False

    @classmethod
    def limpar_cache_local(cls):
        """
        Limpa os dados das tabelas de cache local (leituras e sync_log).
        Não remove a tabela de usuários para manter as credenciais offline.
        """
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM leituras")
                cursor.execute("DELETE FROM sync_log")
                conn.commit()
                logger.info(
                    "🧹 Cache local (leituras e sync_log) limpo com sucesso.")
                return True
        except Exception as e:
            logger.error(f"❌ Erro ao limpar cache local: {e}")
            return False

    @classmethod
    def salvar_leitura(cls, unidade, valor_agua, valor_gas, modo, data_hora,
                       foto_url=None, leiturista=None):
        """Salva uma nova leitura no banco de dados local.

        Unidades duplex (ex: '163/164') são salvas como uma única linha,
        preservando a identidade da unidade igual ao Supabase.
        """
        try:
            # Duplex: mantém "163/164" como unidade_id único (igual ao Supabase)
            tipo_final = f"{modo} (Duplex)" if unidade and "/" in unidade else modo
            valor_leitura = valor_agua if valor_agua is not None else (valor_gas or 0)

            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO leituras
                        (unidade_id, leitura_agua, leitura_gas, tipo,
                         data_hora_coleta, sincronizado, valor_leitura, foto_url, leiturista)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (unidade.strip(), valor_agua, valor_gas, tipo_final,
                      data_hora, 0, valor_leitura, foto_url, leiturista))
                conn.commit()
                logger.debug(f"💾 Leitura salva localmente para unidade {unidade}")
                return {"sucesso": True}

        except Exception as e:
            logging.error(e)
            logger.error(
                f"❌ Erro ao salvar leitura no SQLite (Unidade {unidade}): {str(e)}", exc_info=True)
            from utils.logger_config import enviar_report_erro
            enviar_report_erro(traceback.format_exc(), unidade=unidade)
            return {"sucesso": False, "erro": str(e)}

    @classmethod
    def buscar_historico(cls, unidade):
        """Recupera as últimas leituras para o gráfico."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT data_hora_coleta, leitura_agua, leitura_gas 
                    FROM leituras 
                    WHERE unidade_id = ? 
                    ORDER BY data_hora_coleta DESC 
                    LIMIT 6
                """, (unidade,))
                return [dict(row) for row in cursor.fetchall()][::-1]
        except Exception as e:
            logger.error(f"Erro no histórico: {e}")
            return []

    @classmethod
    def _gerar_lista_unidades(cls):
        """Gera a lista exata do Edifício Vivere com Duplex e Áreas Comuns."""
        try:
            unidades = []

            # APARTAMENTOS (16 andares, final 6 a 1 - Ordem de descida do hall)
            for andar in range(16, 0, -1):
                for final in range(6, 0, -1):
                    u_raw = f"{andar}{final}"

                    # Regra dos Duplex
                    if u_raw in ["163", "164"]:
                        if "163/164" not in unidades:
                            unidades.append("163/164")
                        continue
                    if u_raw in ["23", "24"]:
                        if "23/24" not in unidades:
                            unidades.append("23/24")
                        continue

                    unidades.append(u_raw)

            # ÁREAS COMUNS ao final para encerramento do ciclo
            unidades.append("LAZER GÁS")
            unidades.append("TERREO GERAL ÁGUA")

            # Segurança: Se a lista estiver vazia por algum motivo, não retorna None
            return unidades if unidades else ["ERRO_LISTA_VAZIA"]

        except Exception as e:
            logger.error(f"Erro na lógica de unidades: {e}", exc_info=True)
            return ["ERRO_PROCESSAMENTO"]

    @classmethod
    def get_leituras_mes_atual(cls):
        """Retorna leituras do mês corrente com leitura_anterior via join na tabela de referência."""
        try:
            mes_atual = datetime.now().strftime('%Y-%m')
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT l.id, l.unidade_id, l.leitura_agua, l.leitura_gas,
                           l.data_hora_coleta, l.consumo, l.leiturista,
                           r.leitura_agua AS leitura_anterior_agua,
                           r.leitura_gas  AS leitura_anterior_gas
                    FROM leituras l
                    LEFT JOIN leituras_referencia r ON l.unidade_id = r.unidade_id
                    WHERE l.data_hora_coleta LIKE ?
                    ORDER BY l.data_hora_coleta ASC
                """, (f"{mes_atual}%",))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Erro ao buscar leituras do mês: {e}")
            return []

    @classmethod
    def salvar_referencias_ciclo(cls, dados):
        """
        Salva as leituras do ciclo encerrado como referência (leitura anterior)
        para o próximo ciclo. Chamado antes do reset mensal.
        """
        try:
            refs = {}
            for row in dados:
                uid = row['unidade_id']
                if uid not in refs:
                    refs[uid] = {'agua': None, 'gas': None, 'data': row.get('data_hora_coleta')}
                if row.get('leitura_agua') is not None:
                    refs[uid]['agua'] = row['leitura_agua']
                if row.get('leitura_gas') is not None:
                    refs[uid]['gas'] = row['leitura_gas']

            with cls.get_db() as conn:
                cursor = conn.cursor()
                for uid, vals in refs.items():
                    cursor.execute("""
                        INSERT OR REPLACE INTO leituras_referencia
                            (unidade_id, leitura_agua, leitura_gas, data_referencia)
                        VALUES (?, ?, ?, ?)
                    """, (uid, vals['agua'], vals['gas'], vals.get('data')))
                conn.commit()
            logger.info(f"📌 {len(refs)} referências de leitura salvas para o próximo ciclo.")
            return True
        except Exception as e:
            logger.error(f"Erro ao salvar referências de ciclo: {e}")
            return False

    @classmethod
    def exportar_csv_mes(cls):
        dados = cls.get_leituras_mes_atual()
        caminho = os.path.join(cls.BASE_DIR, "..", "storage",
                               "relatorios", "relatorio_mes.csv")

        with open(caminho, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=dados[0].keys())
            writer.writeheader()
            writer.writerows(dados)
        return caminho

    @classmethod
    def buscar_leituras_periodo(cls, data_inicio, data_fim, unidade=None):
        """
        Busca leituras no SQLite entre duas datas.
        Formato esperado: 'YYYY-MM-DD'
        """
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                # Garantimos que a comparação seja feita apenas na parte da data 'YYYY-MM-DD'
                # para evitar sobreposição de horas em viradas de ciclo.
                query = "SELECT * FROM leituras WHERE substr(data_hora_coleta, 1, 10) BETWEEN ? AND ?"
                params = [data_inicio, data_fim]

                if unidade and unidade != "Geral":
                    query += " AND unidade_id = ?"
                    params.append(unidade)

                query += " ORDER BY data_hora_coleta DESC"
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Erro ao buscar período: {e}")
            return []

    @classmethod
    async def registrar_log_erro(cls, erro, contexto, usuario=None, screenshot_url=None):
        """Registra um erro no Supabase para análise técnica remota."""
        logger.debug(
            f"📡 Tentando registrar log de erro remoto. Contexto: {contexto} | Erro: {erro}")
        try:
            if cls.supabase:
                dados = {
                    "mensagem": str(erro),
                    "contexto": contexto,
                    "usuario": usuario,
                    "data_hora": datetime.now().isoformat()
                }
                cls.supabase.table("logs_erro").insert(dados).execute()
                logger.info(
                    "✅ Log de erro enviado para o Supabase com sucesso.")
        except Exception as e:
            logger.error(
                f"❌ Falha ao enviar log para o Supabase: {e}", exc_info=True)

    @classmethod
    def editar_leitura(cls, leitura_id: int, valor_agua, valor_gas):
        """Atualiza os valores de uma leitura existente e marca como não sincronizada."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE leituras SET leitura_agua=?, leitura_gas=?, sincronizado=0 WHERE id=?",
                    (valor_agua, valor_gas, leitura_id)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Erro ao editar leitura {leitura_id}: {e}")
            return False

    @classmethod
    def deletar_leitura(cls, leitura_id: int):
        """Remove uma leitura do banco local."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM leituras WHERE id=?", (leitura_id,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Erro ao deletar leitura {leitura_id}: {e}")
            return False

    @classmethod
    def buscar_leituras_filtradas(cls, texto=None, unidade=None, mes=None):
        """Busca leituras com filtros opcionais de texto, unidade e mês (YYYY-MM)."""
        try:
            with cls.get_db() as conn:
                cursor = conn.cursor()
                query = """
                    SELECT id, unidade_id, leitura_agua, leitura_gas, tipo,
                           data_hora_coleta, leiturista, sincronizado
                    FROM leituras WHERE 1=1
                """
                params = []
                if unidade and unidade != "Todas":
                    query += " AND unidade_id = ?"
                    params.append(unidade)
                if mes:
                    query += " AND data_hora_coleta LIKE ?"
                    params.append(f"{mes}%")
                if texto:
                    t = f"%{texto}%"
                    query += " AND (unidade_id LIKE ? OR leiturista LIKE ? OR tipo LIKE ?)"
                    params += [t, t, t]
                query += " ORDER BY data_hora_coleta DESC LIMIT 200"
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Erro na busca filtrada: {e}")
            return []

    @classmethod
    async def configurar_db_path(cls, page) -> None:
        """Define DB_PATH com sandbox seguro no mobile ou BASE_DIR no desktop.

        Deve ser chamado em inicializar_background() antes de inicializar_tabelas().
        No Android/iOS usa page.client_storage.get_app_directory() para garantir
        acesso correto ao storage privado do app; no desktop mantém BASE_DIR.
        """
        is_mobile = str(page.platform).lower() in ("android", "ios")
        if is_mobile:
            app_dir = await page.client_storage.get_app_directory()
            cls.DB_PATH = os.path.join(app_dir, "aguaflow.db")
            logger.info(f"📱 Mobile detectado — DB_PATH: {cls.DB_PATH}")
        else:
            cls.DB_PATH = os.path.join(cls.BASE_DIR, "aguaflow.db")
            logger.info(f"🖥️ Desktop detectado — DB_PATH: {cls.DB_PATH}")

    @classmethod
    def upload_foto_hidrometro_sync(cls, caminho_foto: str, unidade: str, modo: str) -> str | None:
        """Upload síncrono da foto do hidrômetro para o bucket fotos_hidrometros no Supabase Storage."""
        try:
            # Usa service role para bypassar RLS no Storage; cai para anon se admin não configurado
            client = cls.supabase_admin or cls.supabase
            if not client or not os.path.exists(caminho_foto):
                return None
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            # Sanitiza: remove chars inválidos para path do Supabase Storage
            import re
            unidade_safe = re.sub(r'[^a-zA-Z0-9_\-/]', '_', unidade)
            storage_path = f"{unidade_safe}/{timestamp}_{modo}.jpg"
            with open(caminho_foto, 'rb') as f:
                dados = f.read()
            client.storage.from_("fotos_hidrometros").upload(
                storage_path,
                dados,
                {"content-type": "image/jpeg", "upsert": "true"}
            )
            url = client.storage.from_("fotos_hidrometros").get_public_url(storage_path)
            logger.info(f"📸 Foto enviada ao Supabase Storage: {url}")
            return url
        except Exception as e:
            logger.error(f"❌ Erro no upload da foto: {e}", exc_info=True)
            return None

# --- FUNÇÃO GLOBAL DE ACESSO ---
# --- FUNÇÃO GLOBAL DE ACESSO ---


def get_supabase_client():
    try:
        # Garante que as chaves do .env foram lidas
        if not hasattr(Database, 'supabase') or Database.supabase is None:
            Database.inicializar_tabelas()  # Força a carga das variáveis e tabelas

        if Database.supabase is None:
            logger.error(
                "ERRO: Supabase não pôde ser inicializado. Verifique seu arquivo .env")
            return None

        return Database.supabase
    except Exception as e:
        logger.critical(
            f"Erro fatal ao conectar ao banco Supabase: {e}", exc_info=True)
        return None


def get_supabase_admin_client():
    """Retorna o cliente Supabase com privilégios de administrador."""
    try:
        if not hasattr(Database, 'supabase_admin') or Database.supabase_admin is None:
            # Tenta inicializar novamente se for None
            Database.inicializar_tabelas()
            if Database.supabase_admin is None:
                logger.error(
                    "ERRO: Supabase Admin não pôde ser inicializado. Verifique SUPABASE_SERVICE_ROLE_KEY.")
                return None
        return Database.supabase_admin
    except Exception as e:
        logger.critical(
            f"Erro fatal ao conectar ao Supabase Admin: {e}", exc_info=True)
        return None
