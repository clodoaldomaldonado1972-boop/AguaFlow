from utils.updater import AppUpdater
from database.database import Database
import sys
import os
import warnings
import asyncio
import flet as ft
import gc

# 1. AJUSTE DE PATH E COMPATIBILIDADE
import os
import sys
import asyncio
import flet as ft
from pathlib import Path
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
        return ft.Text("❌ Supabase: Credenciais não configuradas.", color=ft.colors.RED)

    try:
        client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)
        # Tenta uma operação simples para verificar a conexão e autenticação
        response = client.table('unidades').select('id').limit(1).execute()
        if response.data is not None:
            return ft.Text("✅ Supabase: Conexão e autenticação OK.", color=ft.colors.GREEN)
        else:
            return ft.Text(f"❌ Supabase: Falha na autenticação/acesso. {response.status_code}", color=ft.colors.RED)
    except Exception as e:
        return ft.Text(f"❌ Supabase: Erro de conexão. {e}", color=ft.colors.RED)


async def test_client_storage(page: ft.Page):
    """Testa o funcionamento do client_storage para persistência offline."""
    try:
        await page.client_storage.set_async("test_key", "test_value")
        value = await page.client_storage.get_async("test_key")
        if value == "test_value":
            return ft.Text("✅ Client Storage: Persistência offline OK.", color=ft.colors.GREEN)
        else:
            return ft.Text("❌ Client Storage: Falha na leitura/escrita.", color=ft.colors.RED)
    except Exception as e:
        return ft.Text(f"❌ Client Storage: Erro. {e}", color=ft.colors.RED)


async def test_ocr_engine():
    """
    Testa a disponibilidade do motor de OCR (Tesseract/OpenCV) e binarização adaptativa.
    Nota: Este teste é simulado, pois a verificação real requer a instalação
    e configuração do Tesseract e OpenCV, que pode variar por ambiente.
    """
    try:
        # Lazy load do módulo de visão
        from utils.vision import processar_foto_hidrometro
        # Apenas verifica se a função existe e pode ser chamada (sem execução real)
        if callable(processar_foto_hidrometro):
            return ft.Text("✅ OCR Engine: Módulo de visão computacional disponível.", color=ft.colors.GREEN)
        else:
            return ft.Text("❌ OCR Engine: Módulo de visão computacional não funcional.", color=ft.colors.RED)
    except ImportError:
        return ft.Text("❌ OCR Engine: Módulo 'utils.vision' não encontrado.", color=ft.colors.RED)
    except Exception as e:
        return ft.Text(f"❌ OCR Engine: Erro ao carregar/verificar. {e}", color=ft.colors.RED)


async def test_smtp_email():
    """Testa o envio de e-mail via SMTP (Porta 465) com Senhas de Aplicativo."""
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")
    # Usa o próprio email se destino não for setado
    EMAIL_DESTINO = os.getenv("EMAIL_DESTINO") or EMAIL_USER

    if not EMAIL_USER or not EMAIL_PASS or not EMAIL_DESTINO:
        return ft.Text("❌ SMTP Email: Credenciais de e-mail não configuradas.", color=ft.colors.RED)

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
        return ft.Text("✅ SMTP Email: Envio de e-mail OK.", color=ft.colors.GREEN)
    except Exception as e:
        return ft.Text(f"❌ SMTP Email: Erro ao enviar e-mail. {e}", color=ft.colors.RED)


async def test_sqlite_db():
    """Testa a inicialização e uma operação básica no banco de dados SQLite."""
    try:
        await asyncio.to_thread(Database.init_db)
        # Tenta uma operação simples, como contar unidades
        with Database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM unidades")
            count = cursor.fetchone()[0]
        return ft.Text(f"✅ SQLite DB: Inicialização e acesso OK. ({count} unidades)", color=ft.colors.GREEN)
    except Exception as e:
        return ft.Text(f"❌ SQLite DB: Erro na inicialização/acesso. {e}", color=ft.colors.RED)


async def main(page: ft.Page):
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

    tests = [
        ("Supabase Connection", test_supabase_connection(page)),
        ("Client Storage", test_client_storage(page)),
        ("OCR Engine", test_ocr_engine()),
        ("SMTP Email", test_smtp_email()),
        ("SQLite Database", test_sqlite_db()),
    ]

    detailed_results = ft.Column(
        [ft.Text("Resultados do Checklist:", size=22,
                 weight="bold", color=ft.colors.BLUE_200)],
        horizontal_alignment=ft.CrossAxisAlignment.START,
        scroll=ft.ScrollMode.ALWAYS,
        expand=True
    )

    for test_name, test_coroutine in tests:
        result_text = await test_coroutine
        detailed_results.controls.append(
            ft.Row([ft.Text(f"- {test_name}: "), result_text]))
        page.update()

    results_column.controls.clear()
    results_column.controls.append(detailed_results)
    results_column.controls.append(ft.ElevatedButton(
        "Voltar ao Menu Principal", on_click=lambda _: page.go("/menu")))
    page.update()

if __name__ == "__main__":
    # Para rodar este checklist separadamente, use: python CHECKLIST_MVP.py
    # Ou integre-o ao seu aplicativo Flet.
    ft.app(target=main)
