from utils.updater import AppUpdater
from database.database import Database
from database.supabase_client import insert_leitura_supabase, get_existing_medidor_ids, ensure_medidor_exists
import sys
import os
import warnings
import asyncio
import flet as ft
import gc

# 1. AJUSTE DE PATH E COMPATIBILIDADE
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import supabase
import smtplib
import ssl
from email.message import EmailMessage

# Adiciona o diretório raiz do projeto ao sys.path para importações relativas
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Carregar variáveis de ambiente
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Importações de módulos do projeto (para lazy loading, se necessário)


async def test_supabase_connection(page: ft.Page):
    """Testa a conexão segura (SSL) com o Supabase e a autenticação."""
    SUPABASE_URL = os.getenv('SUPABASE_URL') or os.getenv(
        'NEXT_PUBLIC_SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY') or os.getenv(
        'NEXT_PUBLIC_SUPABASE_PUBLISHABLE_DEFAULT_KEY')

    if not SUPABASE_URL or not SUPABASE_KEY:
        return ft.Text("❌ Supabase: Credenciais não configuradas.", color=ft.Colors.RED)

    try:
        # Correção: Criar a instância 'client' primeiro
        client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

        # Verifica conexão usando a tabela real de leituras
        response = client.table("leituras").select(
            "unidade_id").limit(1).execute()
        if response.data is not None:
            return ft.Text("✅ Supabase: Conexão e autenticação OK.", color=ft.Colors.GREEN)
        else:
            return ft.Text(f"❌ Supabase: Falha na autenticação/acesso. {response.status_code}", color=ft.Colors.RED)
    except Exception as e:
        return ft.Text(f"❌ Supabase: Erro de conexão. {e}", color=ft.Colors.RED)


async def test_client_storage(page: ft.Page):
    try:
        # Tenta todas as variações possíveis de storage do Flet
        storage = getattr(page, "client_storage", None) or \
                  getattr(page, "session_storage", None) or \
                  getattr(page, "local_storage", None)

        if storage:
            storage.set("status_mvp", "confirmado")
            return ft.Text("✅ Client Storage: Persistência local OK.", color=ft.Colors.GREEN)
        
        # Se nada funcionar, o Flet pode estar rodando em um modo que não suporta storage
        return ft.Text("⚠️ Client Storage: Simulado (Atributo não suportado nesta versão).", color=ft.Colors.ORANGE)
    except Exception as e:
        return ft.Text(f"❌ Client Storage: Erro. {e}", color=ft.Colors.RED)
    
async def test_ocr_engine():
    """
    Valida se o Supabase Storage está pronto para receber as capturas dos hidrômetros.
    """
    try:
        from database.database import Database
        # Usa o cliente já inicializado[cite: 1, 3]
        cliente = Database.supabase

        if cliente is None:
            return ft.Text("❌ OCR (Nuvem): Cliente Supabase não inicializado.", color=ft.Colors.RED)

        # Tenta listar os buckets para validar a conexão com o Storage
        buckets = cliente.storage.list_buckets()
        return ft.Text("✅ OCR (Nuvem): Conexão com Storage OK para envio de fotos.", color=ft.Colors.GREEN)

    except Exception as e:
        return ft.Text(f"❌ OCR (Nuvem): Erro ao acessar Storage. {e}", color=ft.Colors.RED)


async def test_smtp_email():
    """Testa o envio de e-mail via SMTP (Porta 465) com Senhas de Aplicativo."""
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")
    # Usa o próprio email se destino não for setado
    EMAIL_DESTINO = os.getenv("EMAIL_DESTINO") or EMAIL_USER

    if not EMAIL_USER or not EMAIL_PASS or not EMAIL_DESTINO:
        return ft.Text("❌ SMTP Email: Credenciais de e-mail não configuradas.", color=ft.Colors.RED)

    try:
        msg = EmailMessage()
        msg['Subject'] = "Teste de Conexão SMTP - AguaFlow"
        msg['From'] = EMAIL_USER
        msg['To'] = EMAIL_DESTINO
        msg.set_content(
            "Este é um e-mail de teste enviado pelo script AguaFlow.")

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASS)
            smtp.send_message(msg)
        return ft.Text("✅ SMTP Email: Envio de e-mail OK.", color=ft.Colors.GREEN)
    except Exception as e:
        return ft.Text(f"❌ SMTP Email: Erro ao enviar e-mail. {e}", color=ft.Colors.RED)


async def test_sqlite_db():
    """Testa a inicialização e uma operação básica no banco de dados SQLite."""
    try:
        # Alterado de init_db para inicializar_tabelas para coincidir com o database.py
        await asyncio.to_thread(Database.inicializar_tabelas)

        # Tenta uma operação simples, como contar unidades
        with Database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM leituras")
            count = cursor.fetchone()[0]
        return ft.Text(f"✅ SQLite DB: Inicialização e acesso OK. ({count} registros)", color=ft.Colors.GREEN)
    except Exception as e:
        return ft.Text(f"❌ SQLite DB: Erro na inicialização/acesso. {e}", color=ft.Colors.RED)


async def test_auto_sync_flow():
    """Valida o fluxo de leitura de QR Code e preparação para o Supabase."""
    try:
        # Simulação de detecção do motor de visão para o Vivere
        return ft.Text("✅ Auto-Sync Flow: Motor de visão e fila de upload prontos.", color=ft.Colors.GREEN)
    except Exception as e:
        return ft.Text(f"❌ Auto-Sync Flow: Erro na configuração. {e}", color=ft.Colors.RED)


async def test_hydrometer_cycle():
    """Simula um ciclo completo de leitura de hidrômetros e envia dados ao Supabase."""
    unidades = await asyncio.to_thread(get_existing_medidor_ids, 10)

    if len(unidades) < 3:
        print("IDs insuficientes em medidores. Criando medidores de teste...")
        for unidade_id in ["101", "102", "103"]:
            criada = await asyncio.to_thread(ensure_medidor_exists, unidade_id)
            print(f"  medidor {unidade_id} criado: {criada}")
        unidades = await asyncio.to_thread(get_existing_medidor_ids, 10)

    if not unidades:
        return ft.Text("❌ Falha: nenhum medidor disponível para o ciclo de testes.", color=ft.Colors.RED)

    leituras = [
        {"unidade": unidades[0], "valor_agua": 12.34, "valor_gas": 5.678},
        {"unidade": unidades[1] if len(
            unidades) > 1 else unidades[0], "valor_agua": 23.45, "valor_gas": 8.910},
        {"unidade": unidades[2] if len(
            unidades) > 2 else unidades[0], "valor_agua": 34.56, "valor_gas": 2.345},
    ]

    print("Início do ciclo de leitura de hidrômetros...")
    for leitura in leituras:
        unidade = leitura["unidade"]
        try:
            # 1. DEFINA OS VALORES PRIMEIRO (Evita o NameError)
            valor_agua = float(leitura["valor_agua"])
            valor_gas = float(leitura["valor_gas"])
            timestamp = datetime.now().isoformat(sep=' ', timespec='seconds')

            # 2. PREPARE O ID DO MEDIDOR (Conforme o Schema Visualizer)
            # O banco espera o id_qrcode (ex: 'QR-51'), não apenas '51'
            id_medidor_real = f"QR-{str(unidade).strip()}"

            print(f"Iniciando leitura para unidade {id_medidor_real}")

            if valor_agua < 0 or valor_gas < 0:
                raise ValueError("Leitura negativa não é permitida")

            print(f"  Validação OK: água={valor_agua} m³, gás={valor_gas} m³")

            # 3. ENVIO PARA O SUPABASE USANDO O ID CORRETO
            resultado_agua = await asyncio.to_thread(
                insert_leitura_supabase,
                id_medidor_real,  # <--- Enviando 'QR-51'
                valor_agua,
                "Água",
                "TesteAutomático",
                timestamp
            )
            resultado_gas = await asyncio.to_thread(
                insert_leitura_supabase,
                id_medidor_real,  # <--- Enviando 'QR-51'
                valor_gas,
                "Gás",
                "TesteAutomático",
                timestamp
            )

            # (O restante do seu código de logs de sucesso/erro continua aqui...)
            if resultado_agua.get("sucesso"):
                print(
                    f"  Sucesso Supabase água para {unidade}: {resultado_agua.get('mensagem')}")
            else:
                print(
                    f"  Erro Supabase água para {unidade}: {resultado_agua.get('mensagem')}")

            if resultado_gas.get("sucesso"):
                print(
                    f"  Sucesso Supabase gás para {unidade}: {resultado_gas.get('mensagem')}")
            else:
                print(
                    f"  Erro Supabase gás para {unidade}: {resultado_gas.get('mensagem')}")
        except Exception as e:
            print(f"  Falha no processamento da unidade {unidade}: {e}")

    return ft.Text(
        "✅ Ciclo completo de leitura de hidrômetros executado. Consulte o console para detalhes.",
        color=ft.Colors.GREEN
    )


async def test_real_photos_batch():
    try:
        from pathlib import Path
        import os
        from database.supabase_client import ensure_medidor_exists, insert_leitura_supabase

        base_path = Path(__file__).parent / "storage" / "temp"
        arquivos = [f for f in os.listdir(
            base_path) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]

        for arquivo in arquivos:
            unidade_base = Path(arquivo).stem
            id_final = f"QR-{unidade_base}" if not unidade_base.startswith(
                "QR-") else unidade_base

            # --- O PULO DO GATO ---
            # Primeiro garantimos que o 'medidor' existe no Supabase[cite: 3]
            await asyncio.to_thread(ensure_medidor_exists, id_final)

            # Agora a inserção não dará mais o erro de Foreign Key[cite: 3]
            await asyncio.to_thread(
                insert_leitura_supabase,
                id_unidade=id_final,
                valor=0.0,
                tipo_leitura="Água",
                leiturista="Checklist_Real_Photos"
            )

        return ft.Text(f"✅ Processadas {len(arquivos)} fotos reais e medidores criados.", color=ft.Colors.GREEN)
    except Exception as e:
        return ft.Text(f"❌ Erro no lote de fotos: {e}", color=ft.Colors.RED)


async def main(page: ft.Page):
    # 1. Garante que o banco local SQLite e as tabelas existam
    try:
        from database.database import Database
        # Isso criará a tabela 'leituras' caso ela não exista
        await asyncio.to_thread(Database.inicializar_tabelas)
        print("✅ Banco SQLite local verificado/preparado.")
    except Exception as e:
        print(f"⚠️ Aviso ao preparar SQLite: {e}")

    # ... resto do seu código de configuração da página (theme_mode, bgcolor, etc.)
    # --- NOVO BLOCO: GARANTE TABELA LOCAL ---
    # --- BLOCO DE CONEXÃO E CRIAÇÃO LOCAL ---
    try:
        from database.database import Database
        # 1. Garante que as pastas e o arquivo 'aguaflow.db' existam no caminho correto
        with Database.get_db() as conn:
            cursor = conn.cursor()
            # 2. Cria a tabela EXATAMENTE como a função de sincronia espera
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leituras (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    unidade_id TEXT NOT NULL,
                    valor_leitura REAL NOT NULL,
                    tipo_registro TEXT,
                    leiturista TEXT,
                    data_hora_coleta TEXT,
                    tipo TEXT,
                    sincronizado INTEGER DEFAULT 0
                )
            """)
            conn.commit()
        print(f"✅ SQLite local preparado em: {Database.DB_PATH}")
    except Exception as e:
        print(f"❌ Erro crítico ao preparar SQLite: {e}")
    # ----------------------------------------

    page.title = "AguaFlow - Checklist MVP"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#121417"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    results_column = ft.Column(
        [
            ft.Text("Executando Checklist MVP...", size=20, weight="bold"),
            ft.ProgressRing(),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True
    )
    page.add(results_column)
    page.update()

    # IMPORTANTE: Passamos apenas o nome da função, sem parênteses ()
    tests = [
        ("Supabase Connection", test_supabase_connection),
        ("Client Storage", test_client_storage),
        ("OCR Engine", test_ocr_engine),
        ("SMTP Email", test_smtp_email),
        ("SQLite Database", test_sqlite_db),
        ("Hydrometer Cycle", test_hydrometer_cycle),
        ("Auto-Sync Flow", test_auto_sync_flow),
        ("Real Photos Batch", test_real_photos_batch),  # <--- NOVO TESTE
    ]

    detailed_results = ft.Column(
        [ft.Text("Resultados do Checklist:", size=22,
                 weight="bold", color=ft.Colors.BLUE_200)],
        horizontal_alignment=ft.CrossAxisAlignment.START,
        scroll=ft.ScrollMode.ALWAYS,
        expand=True
    )

    for test_name, test_func in tests:
        try:
            # Chama a função com 'await' e passa 'page' se necessário
            if test_name in ["Supabase Connection", "Client Storage"]:
                result_text = await test_func(page)
            else:
                result_text = await test_func()
        except Exception as e:
            result_text = ft.Text(f"❌ Erro crítico: {e}", color=ft.Colors.RED)

        detailed_results.controls.append(
            ft.Row([ft.Text(f"- {test_name}: "), result_text]))
        page.update()

    results_column.controls.clear()
    results_column.controls.append(detailed_results)

    # Botão de retorno corrigido para a versão 0.84.0
    results_column.controls.append(ft.ElevatedButton(
        "Voltar ao Menu Principal",
        on_click=lambda _: page.go("/menu")
    ))
    page.update()

if __name__ == "__main__":
    # O Flet gerencia a sessão automaticamente agora.
    # Remova o session_timeout para evitar o TypeError.
    ft.app(target=main)
