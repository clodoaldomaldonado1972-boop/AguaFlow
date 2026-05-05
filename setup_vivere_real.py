import flet as ft
import sqlite3
import random
import os
import pytz
from datetime import datetime

# Configurações Globais
# Garante a existência da pasta antes de qualquer operação de banco de dados
os.makedirs('C:\\AguaFlow', exist_ok=True)

DB_PATH = r"C:\AguaFlow\aguaflow.db"
TZ_SP = pytz.timezone('America/Sao_Paulo')


def inicializar_banco_teste():
    """Garante que a estrutura da tabela esteja pronta para a carga real."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leituras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidade_id TEXT NOT NULL,
            tipo TEXT NOT NULL,
            sincronizado INTEGER DEFAULT 0,
            data_hora_coleta TEXT,
            valor_leitura REAL,
            tipo_registro TEXT
        )
    """)
    conn.commit()
    conn.close()


def executar_carga_vivere():
    """Popula o banco com a malha real de 1 a 16 andares + Áreas Comuns."""
    inicializar_banco_teste()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    unidades_processadas = []

    # 1. Gerar Unidades Habitacionais (16º ao 1º andar)
    for andar in range(16, 0, -1):
        for final in range(6, 0, -1):
            u_raw = f"{andar}{final}"
            if u_raw in ["163", "164"]:
                u_id = "QR-163-164"
            elif u_raw in ["23", "24"]:
                u_id = "QR-23-24"
            else:
                u_id = f"AP-{u_raw}"

            if u_id not in unidades_processadas:
                unidades_processadas.append(u_id)

    # 2. Adicionar Medidores de Área Comum
    unidades_processadas.extend(["LAZER-GAS", "GERAL-AGUA"])

    # 3. Persistência Massiva
    for u in unidades_processadas:
        tipo_reg = random.choice(["Água", "Gás"])
        valor = round(random.uniform(0.100, 850.500), 3)

        # --- CORREÇÃO DO HORÁRIO: DENTRO DO LOOP ---
        # Gera o horário atual, remove o fuso para a string ficar limpa e formata como 'YYYY-MM-DD HH:MM:SS'
        # Dentro do loop 'for u in unidades_processadas':
        data_limpa = datetime.now(TZ_SP).replace(
            tzinfo=None).isoformat(sep=' ', timespec='seconds')
        cursor.execute("""
            INSERT INTO leituras (unidade_id, tipo, valor_leitura, tipo_registro, data_hora_coleta)
            VALUES (?, ?, ?, ?, ?)
        """, (u, "Manual", valor, tipo_reg, data_limpa))

    # ... código anterior dentro de executar_carga_vivere ...
    conn.commit()
    # A linha deve terminar apenas em [0]
    total = cursor.execute("SELECT COUNT(*) FROM leituras").fetchone()[0]
    conn.close()
    print(f'✅ Sucesso: {total} registros inseridos com horário limpo.')


async def main(page: ft.Page):
    page.title = "AguaFlow V1.1.2 - Tecnologia da Informação (Grupo 8)"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 600
    page.window_height = 800

    list_view = ft.ListView(expand=True, spacing=5)

    def carregar_interface(e=None):
        list_view.controls.clear()
        inicializar_banco_teste()

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM leituras ORDER BY id DESC")

        for row in cursor.fetchall():
            u_id = row['unidade_id']
            # Cores Semânticas para Auditoria
            cor = ft.Colors.BLUE_200
            if "QR-" in u_id:
                cor = ft.Colors.AMBER_ACCENT_400  # Destaque Duplex (Amber)
            elif "-" in u_id and "AP" not in u_id:
                cor = ft.Colors.GREEN_ACCENT_400  # Destaque Área Comum (Green)

            list_view.controls.append(
                ft.ListTile(
                    leading=ft.Icon(
                        "qr_code_2" if "QR-" in u_id else "home", color=cor),
                    title=ft.Text(f"Unidade: {u_id}",
                                  color=cor, weight="bold"),
                    subtitle=ft.Text(
                        f"Tipo: {row['tipo_registro']} | Valor: {row['valor_leitura']:.3f} m³"),
                    # Substitua a linha do trailing por esta:
                    trailing=ft.Text(
                        # Extrai apenas '20:17' da string completa
                        value=row['data_hora_coleta'][11:16],
                        size=14,
                        weight="bold",
                        color=ft.Colors.WHITE70
                    )
                )
            )
        conn.close()
        page.update()

    def limpar_reexecutar(e):
        if os.path.exists(DB_PATH):
            try:
                os.remove(DB_PATH)
            except Exception as ex:
                print(f"⚠️ Aviso: Não foi possível deletar o arquivo: {ex}")
        executar_carga_vivere()
        carregar_interface()

    page.add(
        ft.Text("Auditoria de Malha Real - Vivere", size=20, weight="bold"),
        ft.FilledButton("Limpar Banco e Recarregar Malha",
                        icon="sync", on_click=limpar_reexecutar),
        ft.Divider(),
        list_view
    )
    carregar_interface()

if __name__ == "__main__":
    ft.app(target=main)
