async def navegar_menu(perfil):
        """Gerencia o menu principal após o login."""

        async def voltar_e_recarregar(recarregar_medicao=False):
            if recarregar_medicao:
                # Importante: medicao.montar_tela deve ser esperado (await)
                conteudo = await medicao.montar_tela(page, voltar_e_recarregar)
                await carregar_modulo(conteudo)
            else:
                await navegar_menu(perfil)

        # --- FUNÇÕES DE CLIQUE ASYNC (RESOLVE O "NÃO ENTRA") ---
        async def clique_iniciar(e):
            await voltar_e_recarregar(True)

        async def clique_sair(e):
            await iniciar_app()

        # --- COMPONENTES (RESOLVE O "ÍCONES PEQUENOS") ---
        botoes = ft.Column([
            ft.Icon(ft.Icons.WATER_DROP, color="blue", size=100), # Ícone maior para mobile
            ft.Text(f"OPERADOR: {perfil.upper()}",
                    color="white", weight="bold", size=22),
            
            ft.Container(height=20), # Espaçamento
            
            ft.FilledButton(
                "INICIAR LEITURA",
                icon=ft.Icons.QR_CODE_SCANNER,
                width=320, 
                height=70, # Botão bem grande para o polegar
                on_click=clique_iniciar # Chama a função async direta
            ),
            
            ft.TextButton(
                "Sair do Sistema", 
                icon=ft.Icons.LOGOUT,
                on_click=clique_sair
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)

        await carregar_modulo(botoes)