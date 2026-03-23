import flet as ft
import asyncio
from database.database import Database as db


async def montar_tela(page, voltar_ao_menu, on_next=None):
    # --- 1. Busca de Dados ---
    registro = db.buscar_proximo_pendente()
    try:
        # Tenta desempacotar exatamente 3 valores
        id_db, unidade, anterior = registro
    except (ValueError, TypeError):
        id_db, unidade, anterior = None, "Nenhuma pendência", 0.0

    # --- 2. Elementos de Interface (Definidos antes de usar) ---
    txt_valor = ft.TextField(
        label=f"Unidade: {unidade}",
        prefix=ft.Text("m³ "),  # Forma correta nas versões novas
        keyboard_type=ft.KeyboardType.NUMBER,
        width=300
    )
    mensagem_feedback = ft.Text("", weight="bold")
    loading_spinner = ft.ProgressBar(width=300, visible=False)
    cloud_icon = ft.Icon(ft.Icons.CLOUD_QUEUE, color="gray")
    # --- 3. Função de Salvar (DENTRO do escopo da montar_tela) ---

    async def salvar(e):
        if not txt_valor.value:
            txt_valor.error_text = "Informe o valor lido"
            page.update()
            return

        btn_salvar.disabled = True
        loading_spinner.visible = True
        mensagem_feedback.value = "Sincronizando..."
        page.update()

        try:
            # Chama o banco de dados
            resultado = db.registrar_leitura(id_db, txt_valor.value)
            if resultado.get('sucesso'):
                mensagem_feedback.value = "✅ Salvo e Sincronizado!"
                mensagem_feedback.color = "green"
                if resultado.get('supabase_sync'):
                    cloud_icon.color = "green"
                page.update()

                await asyncio.sleep(1.5)
                if on_next:
                    await on_next()
            else:
                mensagem_feedback.value = f"❌ Erro: {resultado.get('mensagem')}"
                mensagem_feedback.color = "red"

        except Exception as err:
            mensagem_feedback.value = f"❗ Falha: {str(err)}"
            mensagem_feedback.color = "red"

        finally:
            btn_salvar.disabled = False
            loading_spinner.visible = False
            page.update()

    # Botão definido após a função salvar
    btn_salvar = ft.ElevatedButton("SALVAR LEITURA", on_click=salvar)

    # --- 4. Layout Final ---
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Medição AguaFlow", size=24, weight="bold"),
                cloud_icon,
                ft.Text(f"Leitura anterior: {anterior}"),
                txt_valor,
                loading_spinner,
                mensagem_feedback,
                ft.Row([
                    btn_salvar,
                    ft.TextButton("Voltar", on_click=voltar_ao_menu)
                ], alignment=ft.MainAxisAlignment.CENTER)
                
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        ),
        padding=20,
        # Isso posiciona exatamente no centro (x=0, y=0)
        alignment=ft.Alignment(0, 0)
    )
