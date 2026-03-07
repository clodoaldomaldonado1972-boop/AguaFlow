import flet as ft
import database as db
import estilos as st


def montar_tela(page, voltar_menu):
    # 1. BUSCA DE DADOS
    unidade = db.buscar_proximo_pendente()

    print(f"DEBUG: Unidade encontrada para ler: {unidade}")

    # 2. TELA DE CONCLUSÃO
    if not unidade:
        return ft.Container(
            expand=True,
            bgcolor="#1A1C1E",
            alignment=ft.Alignment(0, 0),
            content=ft.Column([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color="green", size=80),
                ft.Text("Medição Concluída!", size=24,
                        weight="bold", color="white"),
                ft.ElevatedButton("Voltar ao Menu",
                                  on_click=lambda _: voltar_menu())
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    # 3. MAPEAMENTO DE DADOS
    id_db, nome_unidade, leitura_anterior = unidade[0], unidade[1], unidade[2]

    texto_consumo = ft.Text("Consumo: 0.00 m³", size=18,
                            color=st.COR_PRIMARIA, weight="bold")

    def calcular_ao_digitar(e):
        try:
            if input_valor.value:
                val_limpo = input_valor.value.strip().replace(",", ".")
                atual = float(val_limpo)
                consumo = atual - leitura_anterior
                texto_consumo.value = f"Consumo: {consumo:.2f} m³"
                texto_consumo.color = st.COR_ALERTA if consumo > 20 else st.COR_PRIMARIA
            else:
                texto_consumo.value = "Consumo: 0.00 m³"
        except ValueError:
            texto_consumo.value = "Consumo: ---"
        page.update()

    # 4. CAMPO DE ENTRADA (Ajustado para 7 caracteres)
    input_valor = ft.TextField(
        label="Leitura Atual (m³)",
        keyboard_type=ft.KeyboardType.NUMBER,
        autofocus=True,
        max_length=7,          # Limita a 7 dígitos
        # Para esconder o contador '0/7' sem dar erro de atributo:
        counter=ft.Container(),
        color="white",
        input_filter=ft.InputFilter(
            allow=True,
            regex_string=r"^[0-9]*$",
            replacement_string=""
        ),
        on_change=calcular_ao_digitar,
        on_submit=lambda _: salvar_leitura(None)
    )

    # 5. LÓGICA DE SALVAMENTO (Garantindo a gravação)
    def salvar_leitura(e):
        if not input_valor.value:
            abrir_alerta_pular()
        else:
            try:
                # 1. Limpa o valor e converte
                valor_texto = input_valor.value.strip().replace(",", ".")
                valor = float(valor_texto)

                # 2. GRAVA NO BANCO (O passo crucial que parece estar falhando)
                db.registrar_leitura(id_db, valor)

                # 3. LOG DE CONFIRMAÇÃO NO TERMINAL
                print(f"✅ GRAVADO: Unidade {nome_unidade} com valor {valor}")

                # 4. RECARREGA (Usando o callback do main que definimos)
                voltar_menu(recarregar_medicao=True)

            except ValueError:
                input_valor.error_text = "Número inválido"
                page.update()

    # 6. LAYOUT FINAL
    return ft.Container(
        expand=True,
        bgcolor="#1A1C1E",
        padding=30,
        content=ft.Column(
            controls=[
                ft.Text(f"Unidade: {nome_unidade}",
                        size=28, weight="bold", color="blue"),
                ft.Text(f"Anterior: {leitura_anterior:.2f} m³",
                        size=18, color="white70"),
                ft.Divider(color="white10"),
                input_valor,
                texto_consumo,
                ft.Container(height=20),
                ft.Row([
                    ft.ElevatedButton(
                        "SALVAR", icon=ft.Icons.SAVE, on_click=salvar_leitura, bgcolor="blue", color="white"),
                    ft.IconButton(icon=ft.Icons.SKIP_NEXT, icon_color="orange",
                                  on_click=lambda _: abrir_alerta_pular())
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.TextButton("Sair da Medição",
                              on_click=lambda _: voltar_menu())
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        )
    )
