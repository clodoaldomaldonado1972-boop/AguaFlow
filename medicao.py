import flet as ft
import database as db

def montar_tela(page, voltar_menu):
    """
    Constrói a interface de medição. 
    Busca automaticamente a próxima unidade pendente no banco de dados.
    """
    
    # 1. BUSCA DE DADOS: Puxa a próxima unidade que ainda não tem 'leitura_atual'
    unidade = db.buscar_proximo_pendente()
    
    # 2. VALIDAÇÃO: Se 'unidade' for None, significa que o trabalho do mês acabou
    if not unidade:
        return ft.Container(
            content=ft.Column([
                ft.Icon("check_circle", color="green", size=60),
                ft.Text("Medição Concluída!", size=20, weight="bold"),
                ft.Text("Todas as unidades foram lidas.", color="grey"),
                # Botão para retornar ao menu principal (main.py)
                ft.FilledButton("Voltar ao Menu", 
                    on_click=lambda _: (page.controls.clear(), voltar_menu(), page.update()))
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=50
        )

    # 3. MAPEAMENTO: Extrai os dados da tupla vinda do banco (ID, Nome, Leitura Anterior)
    id_db, nome_unidade, leitura_anterior = unidade[0], unidade[1], unidade[2]
    
    # Label dinâmico que mostra o cálculo de consumo em tempo real
    texto_consumo = ft.Text("Consumo: 0.00 m³", size=18, color="blue", weight="bold")
    
    def calcular_ao_digitar(e):
        """Calcula o consumo instantaneamente enquanto o usuário digita."""
        try:
            if input_valor.value:
                # Sanitização: remove espaços e garante ponto decimal para o Python
                val_limpo = input_valor.value.strip().replace(",", ".")
                atual = float(val_limpo)
                
                # Regra de negócio: Consumo = Leitura Atual - Leitura do mês anterior
                consumo = atual - leitura_anterior
                texto_consumo.value = f"Consumo: {consumo:.2f} m³"
                
                # Alerta visual: se o consumo for alto (>20), o texto fica vermelho
                texto_consumo.color = "red" if consumo > 20 else "blue"
            else:
                texto_consumo.value = "Consumo: 0.00 m³"
        except ValueError:
            texto_consumo.value = "Consumo: ---"
        page.update()

    # 4. COMPONENTE DE ENTRADA: Campo de texto otimizado para números
    input_valor = ft.TextField(
        label="Leitura Atual (m³)", 
        keyboard_type=ft.KeyboardType.NUMBER, # Abre teclado numérico no celular
        autofocus=True,                       # Foca o campo assim que a tela abre
        max_length=7,                         # Evita erros de digitação excessiva
        # Filtro: só permite números, pontos e vírgulas
        input_filter=ft.InputFilter(allow=True, regex_string=r"^[0-9,.]*$", replacement_string=""),
        on_change=calcular_ao_digitar,
        on_submit=lambda _: salvar_leitura(None) # Salva ao apertar 'Enter'
    )

    def salvar_leitura(e):
        """Grava os dados no SQLite e recarrega a tela para a próxima unidade."""
        if not input_valor.value:
            abrir_alerta_pular() # Se estiver vazio, pergunta se quer pular
        else:
            try:
                valor = float(input_valor.value.replace(",", "."))
                # Envia para o módulo database.py salvar no banco
                db.registrar_leitura(id_db, valor)
                
                # RECURSIVIDADE: Limpa a tela e chama 'montar_tela' de novo para a próxima unidade
                page.controls.clear()
                page.add(montar_tela(page, voltar_menu))
                page.update()
            except ValueError:
                input_valor.error_text = "Número inválido"
                page.update()

    def abrir_alerta_pular():
        """Cria um diálogo de confirmação para pular unidades inacessíveis."""
        def confirmar_pulo(e):
            # Registra como 0.0 e marca status 'pulado' para o relatório
            db.registrar_leitura(id_db, 0.0, status="pulado")
            dlg.open = False
            page.controls.clear()
            page.add(montar_tela(page, voltar_menu))
            page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Pular Unidade?"),
            content=ft.Text(f"Deseja pular o apto {nome_unidade}?"),
            actions=[
                ft.TextButton("Sim, Pular", on_click=confirmar_pulo),
                ft.TextButton("Cancelar", on_click=lambda _: (setattr(dlg, "open", False), page.update()))
            ]
        )
        page.dialog = dlg
        dlg.open = True
        page.update()

    # 5. LAYOUT FINAL: Organização visual dos elementos na tela
    return ft.Container(
        padding=30,
        content=ft.Column([
            ft.Text(f"Unidade: {nome_unidade}", size=30, weight="bold"),
            ft.Text(f"Leitura Anterior: {leitura_anterior:.2f} m³", size=16, color="grey"),
            ft.Divider(),
            input_valor,
            texto_consumo,
            ft.Row([
                ft.FilledButton(
                    "SALVAR", 
                    on_click=salvar_leitura, 
                    style=ft.ButtonStyle(bgcolor="green", color="white"), 
                    expand=True
                ),
                ft.IconButton(
                    icon="skip_next", 
                    on_click=lambda _: abrir_alerta_pular(), 
                    icon_color="red",
                    tooltip="Pular esta unidade"
                ),
            ]),
            # Botão de emergência para sair do fluxo de medição
            ft.TextButton("Interromper e Sair", 
                on_click=lambda _: (page.controls.clear(), voltar_menu(), page.update()))
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )