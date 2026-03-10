import flet as ft
import database as db

# Definição de cores padrão do sistema
COR_PRIMARIA = "blue"
COR_ALERTA = "orange"


def montar_tela(page, voltar_menu):
    # 1. BUSCA DE DADOS: Procura no banco de dados a próxima unidade que ainda não foi lida
    unidade = db.buscar_proximo_pendente()

    # 2. VERIFICAÇÃO DE CONCLUSÃO: Se não houver mais unidades, mostra a tela de sucesso
    if not unidade:
        return ft.Container(
            expand=True, bgcolor="#1A1C1E", alignment=ft.Alignment(0, 0),
            content=ft.Column([
                ft.Icon(ft.Icons.CHECK_CIRCLE, color="green", size=80),
                ft.Text("Todas as medições concluídas!",
                        size=24, weight="bold", color="white"),
                ft.ElevatedButton("Voltar ao Menu",
                                  on_click=lambda _: voltar_menu())
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )

    # MAPEAMENTO: Extrai os dados da unidade atual vinda do banco
    id_db, nome_unidade, leitura_anterior = unidade[0], unidade[1], unidade[2]

    # --- NOVO: COMPONENTE DE CÂMERA PARA CELULAR (WEB NATIVE) ---
    # Diferente do OpenCV (que busca a câmera do PC), este componente
    # aciona o hardware do dispositivo que está acessando o navegador (seu Samsung M14).
    camera_mobile = ft.Camera(
        visible=False,  # Começa invisível para não atrapalhar o formulário
        on_update=lambda e: print("O celular ativou o hardware de vídeo."),
    )

    # Adicionamos a câmera ao 'overlay' (camada flutuante) da página para ela poder aparecer por cima
    if camera_mobile not in page.overlay:
        page.overlay.append(camera_mobile)

    # --- FUNÇÕES DE LÓGICA ---

    def calcular_ao_digitar(e):
        """Calcula o consumo em tempo real conforme o operador digita no celular."""
        try:
            input_valor.error_text = ""
            if input_valor.value:
                # Troca vírgula por ponto para o Python conseguir calcular
                val_limpo = input_valor.value.replace(",", ".")
                atual = float(val_limpo)
                consumo = atual - leitura_anterior

                texto_consumo.value = f"Consumo: {consumo:.2f} m³"
                # Se o consumo for maior que 20m³ ou negativo, fica laranja (alerta)
                texto_consumo.color = COR_ALERTA if consumo > 20 or consumo < 0 else COR_PRIMARIA
            else:
                texto_consumo.value = "Consumo: 0.00 m³"
        except ValueError:
            texto_consumo.value = "Consumo: ---"
        page.update()

    def abrir_camera_mobile(e):
        """Ativa a câmera do navegador. Como o link é HTTPS (Ngrok), o Chrome do celular pedirá permissão."""
        camera_mobile.visible = True
        page.update()

    # --- COMPONENTES VISUAIS ---

    texto_consumo = ft.Text("Consumo: 0.00 m³", size=18,
                            color=COR_PRIMARIA, weight="bold")

    input_valor = ft.TextField(
        label="Leitura Atual (m³)",
        keyboard_type=ft.KeyboardType.NUMBER,  # Abre o teclado numérico no celular
        width=250,
        color="white",
        on_change=calcular_ao_digitar,
    )

    # Organiza o campo de texto e o botão da câmera lado a lado
    linha_input_ocr = ft.Row([
        input_valor,
        ft.IconButton(
            icon=ft.Icons.CAMERA_ALT,
            icon_color="blue",
            on_click=abrir_camera_mobile,  # Aciona a câmera do dispositivo mobile
            tooltip="Abrir câmera do celular"
        )
    ], alignment=ft.MainAxisAlignment.CENTER)

    def salvar_leitura(e):
        """Valida e grava a medição no banco de dados."""
        if not input_valor.value:
            abrir_alerta_pular()
        else:
            try:
                valor = float(input_valor.value.strip().replace(",", "."))
                db.registrar_leitura(id_db, valor)
                # Volta e carrega a próxima unidade
                voltar_menu(recarregar_medicao=True)
            except ValueError:
                input_valor.error_text = "Número inválido"
                page.update()

    def abrir_alerta_pular():
        """Cria um aviso caso o operador queira pular a unidade atual."""
        def confirmar_pulo(e):
            dlg.open = False
            db.registrar_leitura(id_db, 0.0, status="pulado")
            page.update()
            voltar_menu(recarregar_medicao=True)

        dlg = ft.AlertDialog(
            title=ft.Text("Pular Unidade?"),
            content=ft.Text(f"Deseja pular a unidade {nome_unidade}?"),
            actions=[
                ft.TextButton("Sim, Pular", on_click=confirmar_pulo),
                ft.TextButton("Cancelar", on_click=lambda _: (
                    setattr(dlg, "open", False), page.update()))
            ]
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    # RETORNO DA INTERFACE: O Container principal que o celular irá renderizar
    return ft.Container(
        expand=True, bgcolor="#1A1C1E", padding=30,
        content=ft.Column(
            controls=[
                ft.Text(f"Unidade: {nome_unidade}",
                        size=28, weight="bold", color="blue"),
                ft.Text(f"Anterior: {leitura_anterior:.2f} m³",
                        size=18, color="white70"),
                ft.Divider(color="white10"),

                linha_input_ocr,  # Mostra o campo de entrada e o botão da câmera
                texto_consumo,   # Mostra o cálculo do consumo

                ft.Container(height=20),  # Espaçamento

                ft.Row([
                    ft.FilledButton("SALVAR LEITURA", icon=ft.Icons.SAVE,
                                    on_click=salvar_leitura, width=200),
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
