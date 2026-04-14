import flet as ft
import asyncio
from database.database import Database
from views import styles as st

def montar_tela_medicao(page: ft.Page, on_back_click=None):
    # 1. Lista estática ordenada seguindo a regra do hall (166-161... 16-11)
    db_lista = Database._gerar_lista_unidades()
    
    # --- COMPONENTES DE INTERFACE ---
    txt_unidade = st.campo_estilo("Unidade Atual", ft.icons.HOME, read_only=True)
    
    # Campos com trava de entrada para no máximo 2 casas decimais
    txt_agua = st.campo_estilo(
        "Leitura Água (*)", 
        ft.icons.WATER_DROP, 
        keyboard_type=ft.KeyboardType.NUMBER
    )
    txt_agua.input_filter = ft.InputFilter(
        allow=True, 
        regex_string=r"^\d*[.,]?\d{0,2}$", 
        replacement_string=""
    )

    txt_gas = st.campo_estilo(
        "Leitura Gás (Opcional)", 
        ft.icons.LOCAL_GAS_STATION, 
        keyboard_type=ft.KeyboardType.NUMBER
    )
    txt_gas.input_filter = ft.InputFilter(
        allow=True, 
        regex_string=r"^\d*[.,]?\d{0,2}$", 
        replacement_string=""
    )
    
    lbl_status = ft.Text("Pronto para medição", weight="bold", size=14, color=ft.colors.BLUE_200)

    # Som de Alerta (Certifica-te que tens o ficheiro assets/alerta.mp3)
    audio_alerta = ft.Audio(src="assets/alerta.mp3", autoplay=False)
    page.overlay.append(audio_alerta)

    # --- LÓGICA DE APOIO ---

    def disparar_alerta(mensagem):
        """Dispara aviso visual e sonoro."""
        audio_alerta.play()
        page.snack_bar = ft.SnackBar(
            content=ft.Text(mensagem), 
            bgcolor=ft.colors.ERROR
        )
        page.snack_bar.open = True
        page.update()

    def validar_pulo_unidade(unidade_atual):
        """Verifica se o zelador esqueceu alguma unidade do hall anterior."""
        ultima_lida = Database.buscar_ultima_unidade_lida()
        if not ultima_lida or ultima_lida not in db_lista:
            return True
            
        idx_ultima = db_lista.index(ultima_lida)
        idx_atual = db_lista.index(unidade_atual)
        
        # Se o índice atual for maior que o próximo esperado (idx_ultima + 1)
        if idx_atual > idx_ultima + 1:
            unidade_esquecida = db_lista[idx_ultima + 1]
            disparar_alerta(f"PULO DETECTADO! A unidade {unidade_esquecida} ainda não foi lida.")
            return False
        return True

    # --- FUNÇÃO PRINCIPAL DE SALVAMENTO ---

    async def realizar_salvamento(e):
        # 1. Validação e Trava de 2 casas decimais
        if not txt_agua.value:
            disparar_alerta("A leitura de ÁGUA é obrigatória!")
            return

        try:
            # Substitui vírgula por ponto e trava em 2 casas decimais
            v_agua = round(float(txt_agua.value.replace(',', '.')), 2)
            v_gas = round(float(txt_gas.value.replace(',', '.')), 2) if txt_gas.value else None

            # 2. Validação de Pulo (Garante a sequência correta do hall)
            if not validar_pulo_unidade(txt_unidade.value):
                return

            # 3. Gravação no Banco de Dados
            res = Database.registrar_leitura(
                unidade=txt_unidade.value,
                valor_agua=v_agua,
                valor_gas=v_gas
            )

            if res['sucesso']:
                # --- LÓGICA DE AVANÇO AUTOMÁTICO ---
                atual_idx = db_lista.index(txt_unidade.value)
                
                if atual_idx + 1 < len(db_lista):
                    # Localiza e passa para a próxima unidade da lista estática
                    proxima = db_lista[atual_idx + 1]
                    txt_unidade.value = proxima
                    txt_agua.value = "" # Limpa para a nova leitura
                    txt_gas.value = ""  # Limpa para a nova leitura
                    lbl_status.value = f"✅ Salvo! Próxima: {proxima}"
                    lbl_status.color = "green"
                else:
                    # Chegou ao fim da lista (Geral Água)
                    lbl_status.value = "Leituras concluídas com sucesso!"
                    lbl_status.color = "blue"
                    page.update()
                    await asyncio.sleep(1.5)
                    page.go("/relatorios")
            else:
                disparar_alerta(res['mensagem'])

        except ValueError:
            disparar_alerta("Erro: Insira valores numéricos válidos.")
        
        page.update()

    # --- INICIALIZAÇÃO DA TELA ---
    ultima = Database.buscar_ultima_unidade_lida()
    # Define a unidade inicial baseada na última gravada ou começa na 166
    if ultima and ultima in db_lista:
        idx_prox = db_lista.index(ultima) + 1
        txt_unidade.value = db_lista[idx_prox] if idx_prox < len(db_lista) else db_lista[-1]
    else:
        txt_unidade.value = db_lista[0]

    # --- CONSTRUÇÃO DA VIEW ---
    return ft.View(
        route="/medicao",
        bgcolor=st.BG_DARK,
        controls=[
            ft.AppBar(
                title=ft.Text("Medição AguaFlow"), 
                bgcolor=ft.colors.BLUE_900,
                leading=ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: page.go("/menu"))
            ),
            ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.icons.SPEED, size=50, color="blue"),
                        ft.Text("Registo de Consumo", size=20, weight="bold"),
                        ft.Divider(height=10, color="transparent"),
                        txt_unidade,
                        txt_agua,
                        txt_gas,
                        lbl_status,
                        ft.Divider(height=20),
                        ft.ElevatedButton(
                            "CONFIRMAR E SALVAR", 
                            icon=ft.icons.SAVE, 
                            width=320,
                            height=50,
                            style=st.BTN_MAIN,
                            on_click=lambda e: page.run_task(realizar_salvamento, e)
                        ),
                        ft.TextButton("Cancelar", on_click=lambda _: page.go("/menu"))
                    ], horizontal_alignment="center", spacing=15),
                    padding=30,
                    bgcolor=ft.colors.with_opacity(0.05, "white"),
                    border_radius=20
                )
            ], horizontal_alignment="center", scroll=ft.ScrollMode.AUTO)
        ]
    )