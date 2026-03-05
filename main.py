import flet as ft
import database as db
import vision
import reports

# Definição de Cores Identificadas nas Imagens
NAVY_BLUE = "#002868"
BG_WHITE = "#F8F9FA"

def main(page: ft.Page):
    page.title = "ÁguaFlow - Vivere Prudente"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Ajuste para visualização mobile e centralização
    page.window_width = 400
    page.window_height = 750
    page.bgcolor = BG_WHITE
    page.scroll = "adaptive"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # --- COMPONENTES VISUAIS (ESTILO) ---
    
    def header(titulo):
        """Cria a barra superior Navy Blue com bordas arredondadas embaixo"""
        return ft.Container(
            content=ft.Text(titulo, color="white", weight="bold", size=18, text_align="center"),
            bgcolor=NAVY_BLUE,
            padding=20,
            border_radius=ft.border_radius.only(bottom_left=15, bottom_right=15),
            alignment=ft.alignment.center,
            width=float("inf"),
        )

    def input_field(label, value="", is_readonly=False, icon=None, ref=None):
        """Cria campos com bordas grossas (2px) e cantos arredondados (12)"""
        return ft.Column([
            ft.Text(label, color=NAVY_BLUE, weight="bold", size=12),
            ft.Container(
                content=ft.Row([
                    ft.Icon(icon, color=NAVY_BLUE) if icon else ft.Container(),
                    ft.TextField(
                        ref=ref,
                        value=str(value),
                        border=ft.InputBorder.NONE,
                        read_only=is_readonly,
                        # Força o teclado numérico no celular
                        keyboard_type=ft.KeyboardType.NUMBER,
                        text_style=ft.TextStyle(size=18, weight="bold", color="black"),
                        expand=True,
                    )
                ]),
                border=ft.border.all(2, NAVY_BLUE),
                border_radius=12,
                padding=ft.padding.symmetric(horizontal=15, vertical=5),
                bgcolor="white" if not is_readonly else "#E9ECEF"
            )
        ], spacing=5, width=320)

    # --- LÓGICA DE AÇÕES ---

    def acionar_camera(leitura_ref):
        """Simula a abertura da câmera e preenche o campo"""
        # Aqui chamamos o seu módulo vision
        vision.escanear_qr() 
        # Como é um simulador, vamos colocar um valor fixo de exemplo
        leitura_ref.current.value = "00481533"
        page.update()

    def salvar_e_proximo(id_apto, txt_leitura):
        """Valida, salva no banco e avança para a próxima unidade"""
        if not txt_leitura.value:
            page.snack_bar = ft.SnackBar(ft.Text("⚠️ Digite a leitura atual!"), bgcolor="orange")
            page.snack_bar.open = True
            page.update()
            return

        try:
            valor = float(txt_leitura.value.replace(",", "."))
            db.salvar_leitura(id_apto, valor)
            
            page.snack_bar = ft.SnackBar(ft.Text("✅ Leitura Salva com Sucesso!"), bgcolor="green")
            page.snack_bar.open = True
            
            # Avança automaticamente para o próximo
            mostrar_leitura_individual() 
        except ValueError:
            page.snack_bar = ft.SnackBar(ft.Text("❌ Erro: Use apenas números!"), bgcolor="red")
            page.snack_bar.open = True
        page.update()

    def enviar_relatorio_final(e):
        """Processo de geração e envio de e-mail"""
        # Feedback visual de processamento
        page.snack_bar = ft.SnackBar(ft.Text("⏳ Gerando PDF e enviando e-mail..."), duration=3000)
        page.snack_bar.open = True
        page.update()

        dados = db.buscar_todos()
        if not dados: return

        pdf = reports.gerar_relatorio_leituras_pdf(dados)
        sucesso = reports.enviar_email_com_pdf("clodoaldomaldonado112@gmail.com", pdf)
        
        page.clean()
        mostrar_inicio()
        
        page.snack_bar = ft.SnackBar(
            ft.Text("📧 Relatório enviado!" if sucesso else "❌ Erge no envio."),
            bgcolor="green" if sucesso else "red"
        )
        page.snack_bar.open = True
        page.update()

    # --- TELAS ---

    def mostrar_leitura_individual():
        page.clean()
        unidade = db.buscar_proximo_pendente() 
        
        if not unidade:
            page.add(
                header("CONCLUÍDO"),
                ft.Column([
                    ft.Divider(height=50, color="transparent"),
                    ft.Icon(ft.icons.CHECK_CIRCLE, color="green", size=100),
                    ft.Text("Todas as unidades lidas!", size=22, weight="bold"),
                    ft.ElevatedButton(
                        "GERAR RELATÓRIO PDF", 
                        on_click=enviar_relatorio_final,
                        bgcolor=NAVY_BLUE, color="white", height=50
                    ),
                    ft.TextButton("Voltar", on_click=lambda _: mostrar_inicio())
                ], horizontal_alignment="center", spacing=20)
            )
        else:
            leitura_ref = ft.Ref[ft.TextField]()
            todos = db.buscar_todos()
            detalhe = next((x for x in todos if x[0] == unidade[0]), None)
            anterior = detalhe[4] if detalhe else 0

            page.add(
                header("LEITURA DE HIDRÔMETROS"),
                ft.Column([
                    ft.Text(f"Unidade {unidade[1]}", size=32, weight="bold", color="black"),
                    ft.Text(f"Bloco {unidade[2]}", size=16, color="grey"),
                    
                    # Botão para simular o Scanner
                    ft.IconButton(
                        icon=ft.icons.CAMERA_ALT_ROUNDED, 
                        icon_color=NAVY_BLUE, 
                        icon_size=40,
                        tooltip="Escanear Hidrômetro",
                        on_click=lambda _: acionar_camera(leitura_ref)
                    ),

                    input_field("LEITURA ATUAL", icon=ft.icons.WATER_DROP, ref=leitura_ref),
                    input_field("LEITURA ANTERIOR", value=f"{anterior} m³", is_readonly=True),
                    
                    ft.Container(
                        content=ft.Text("SALVAR E PRÓXIMO", color="white", weight="bold"),
                        bgcolor=NAVY_BLUE,
                        padding=20,
                        border_radius=12,
                        width=320,
                        alignment=ft.alignment.center,
                        on_click=lambda _: salvar_e_proximo(unidade[0], leitura_ref.current)
                    ),
                    ft.TextButton("Menu Inicial", on_click=lambda _: mostrar_inicio())
                ], horizontal_alignment="center", spacing=15)
            )
        page.update()

    def mostrar_inicio():
        page.clean()
        page.add(
            header("ÁGUAFLOW - VIVERE PRUDENTE"),
            ft.Column([
                ft.Divider(height=30, color="transparent"),
                ft.Icon(ft.icons.WATER_DROP_ROUNDED, size=80, color=NAVY_BLUE),
                ft.Text("Sistema de Gestão", size=24, weight="bold", color=NAVY_BLUE),
                ft.Divider(height=20, color="transparent"),
                
                ft.ElevatedButton(
                    "INICIAR LEITURAS", 
                    on_click=lambda _: mostrar_leitura_individual(),
                    width=300, height=60, bgcolor=NAVY_BLUE, color="white",
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12))
                ),
                ft.OutlinedButton(
                    "ENVIAR RELATÓRIO", 
                    on_click=enviar_relatorio_final,
                    width=300, height=60, 
                    style=ft.ButtonStyle(
                        side=ft.BorderSide(2, NAVY_BLUE),
                        shape=ft.RoundedRectangleBorder(radius=12)
                    )
                ),
                ft.Text("v1.0.4 - Operacional", size=10, color="grey")
            ], horizontal_alignment="center", spacing=15)
        )
        page.update()

    mostrar_inicio()

if __name__ == "__main__":
    db.init_db()
    ft.app(target=main)
    