import flet as ft
import asyncio
from database.database import Database as db

async def montar_tela(page, voltar_ao_menu, on_next=None):
    # --- 1. Busca de Dados ---
    registro = db.buscar_proximo_pendente()
    try:
        id_db, unidade, anterior = registro
    except (ValueError, TypeError):
        id_db, unidade, anterior = None, "Nenhuma pendência", 0.0

    # --- 2. Elementos de Interface ---
    txt_valor = ft.TextField(
        label=f"Unidade: {unidade}",
        prefix=ft.Text("m³ "),
        keyboard_type=ft.KeyboardType.NUMBER,
        width=300
    )
    mensagem_feedback = ft.Text("", weight="bold")
    loading_spinner = ft.ProgressBar(width=300, visible=False)
    cloud_icon = ft.Icon(ft.Icons.CLOUD_QUEUE, color="gray")

    # Variável de controle de processamento (cadeado)
    state = {"processando": False}

    # --- 3. Função de Salvar ---
    async def salvar(e):
        if state["processando"]:
            return
            
        if not txt_valor.value:
            txt_valor.error_text = "Informe o valor lido"
            page.update()
            return

        # 1. Tratamento do número (Força 2 casas decimais)
        try:
            valor_bruto = txt_valor.value.replace(",", ".")
            valor_final = float("{:.2f}".format(float(valor_bruto)))
        except ValueError:
            txt_valor.error_text = "Digite um número válido"
            page.update()
            return

        # Ativa trava e interface
        state["processando"] = True
        btn_salvar.disabled = True
        loading_spinner.visible = True
        mensagem_feedback.value = "Sincronizando..."
        page.update()

        try:
            # Envia para o banco
            resultado = db.registrar_leitura(id_db, valor_final)
            
            if resultado.get('sucesso'):
                mensagem_feedback.value = "✅ Salvo e Sincronizado!"
                mensagem_feedback.color = "green"
                if resultado.get('supabase_sync'):
                    cloud_icon.color = "green"
                page.update()

                await asyncio.sleep(1.0)
                if on_next:
                    await on_next()
            else:
                mensagem_feedback.value = f"❌ Erro: {resultado.get('mensagem')}"
                mensagem_feedback.color = "red"
                btn_salvar.disabled = False # Reativa para tentar de novo

        except Exception as err:
            mensagem_feedback.value = f"❗ Falha: {str(err)}"
            mensagem_feedback.color = "red"
            btn_salvar.disabled = False

        finally:
            state["processando"] = False
            loading_spinner.visible = False
            page.update()

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
        alignment=ft.Alignment(0, 0)
    )
    