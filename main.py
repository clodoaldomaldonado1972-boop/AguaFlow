import flet as ft
import database as db
import vision
import reports
import os

# Definição de Cores Identificadas nas Imagens
NAVY_BLUE = "#002868"
BG_WHITE = "#F8F9FA"

def main(page: ft.Page):
    page.title = "ÁguaFlow - Vivere Prudente"
    page.theme_mode = ft.ThemeMode.LIGHT
    # Ajuste para parecer um aplicativo de celular
    page.window_width = 400
    page.window_height = 700
    page.bgcolor = BG_WHITE
    page.scroll = "adaptive"

    # --- COMPONENTES VISUAIS (ESTILO) ---
    
    def header(titulo):
        """Cria a barra superior azul marinho do projeto"""
        return ft.Container(
            content=ft.Text(titulo, color="white", weight="bold", size=18, text_align="center"),
            bgcolor=NAVY_BLUE,
            padding=15,
            border_radius=ft.border_radius.only(bottom_left=15, bottom_right=15),
            alignment=ft.alignment.center,
            margin=ft.margin.only(bottom=10)
        )

    def input_field(label, value="", is_readonly=False, icon=None, ref=None):
        """Cria os campos arredondados com borda azul conforme as fotos"""
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
                        text_style=ft.TextStyle(size=18, weight="bold", color="black"),
                        expand=True,
                    )
                ]),
                border=ft.border.all(2, NAVY_BLUE),
                border_radius=12,
                padding=ft.padding.symmetric(horizontal=15, vertical=2),
                bgcolor="white" if not is_readonly else "#E9ECEF"
            )
        ], spacing=5)

    # --- LÓGICA DE TRANSIÇÃO DE TELAS ---

    def salvar_e_proximo(id_apto, txt_leitura):
        """Lógica para salvar no banco e pular para o próximo"""
        try:
            valor = float(txt_leitura.value)
            db.salvar_leitura(id_apto, valor)
            page.snack_bar = ft.SnackBar(ft.Text("✅ Leitura Salva!"), bgcolor="green")
            page.snack_bar.open = True
            mostrar_leitura_individual() # Recarrega a tela com o próximo pendente
        except:
            page.snack_bar = ft.SnackBar(ft.Text("⚠️ Digite um valor numérico válido!"), bgcolor="red")
            page.snack_bar.open = True
        page.update()

    def enviar_relatorio_final(e):
        """Gera o PDF real e envia por e-mail"""
        dados = db.buscar_todos()
        pdf = reports.gerar_relatorio_leituras_pdf(dados)
        sucesso = reports.enviar_email_com_pdf("clodoaldomaldonado112@gmail.com", pdf)
        
        if sucesso:
            page.snack_bar = ft.SnackBar(ft.Text("📧 Relatório enviado com sucesso!"), bgcolor="green")
        else:
            page.snack_bar = ft.SnackBar(ft.Text("❌ Erro ao enviar e-mail."), bgcolor="red")
        page.snack_bar.open = True
        mostrar_inicio()

    # --- TELAS ---

    def mostrar_leitura_individual():
        page.clean()
        unidade = db.buscar_proximo_pendente() # Busca id, numero, bloco
        
        if not unidade:
            page.add(
                header("LEITURA CONCLUÍDA"),
                ft.Column([
                    ft.Icon(ft.icons.CHECK_CIRCLE, color="green", size=80),
                    ft.Text("Todas as unidades foram lidas!", size=20, weight="bold", text_align="center"),
                    ft.FilledButton("VOLTAR AO INÍCIO", on_click=lambda _: mostrar_inicio(), bgcolor=NAVY_BLUE)
                ], horizontal_alignment="center", spacing=20)
            )
        else:
            # Referência para pegar o valor digitado
            leitura_ref = ft.Ref[ft.TextField]()
            
            # Aqui pegamos a leitura anterior do banco para exibir (opcional)
            # Como buscar_proximo_pendente retorna (id, num, bloco), vamos buscar os detalhes:
            todos = db.buscar_todos()
            detalhe = next((x for x in todos if x[0] == unidade[0]), None)
            anterior = detalhe[4] if detalhe else 0

            page.add(
                ft.Column([
                    header("LEITURA DE HIDRÔMETROS"),
                    ft.Text(f"Unidade {unidade[1]}", size=30, weight="bold", color="black"),
                    ft.Text(f"Bloco {unidade[2]}", size=16, color="grey"),
                    
                    input_field("LEITURA ATUAL", icon=ft.icons.WATER_DROP, ref=leitura_ref),
                    ft.Divider(height=10, color="transparent"),
                    input_field("LEITURA ANTERIOR", value=anterior, is_readonly=True),
                    
                    ft.Container(
                        content=ft.Text("SALVAR LEITURA", color="white", weight="bold", size=16),
                        bgcolor=NAVY_BLUE,
                        padding=20,
                        border_radius=12,
                        alignment=ft.alignment.center,
                        on_click=lambda _: salvar_e_proximo(unidade[0], leitura_ref.current)
                    ),
                    ft.TextButton("Cancelar e Voltar", on_click=lambda _: mostrar_inicio())
                ], horizontal_alignment="center", spacing=10)
            )
        page.update()

    def mostrar_inicio():
        page.clean()
        page.add(
            header("ÁGUAFLOW - VIVERE PRUDENTE"),
            ft.Container(
                content=ft.Column([
                    ft.Image(src="https://cdn-icons-png.flaticon.com/512/3105/3105807.png", width=100), # Ícone ilustrativo
                    ft.ElevatedButton(
                        "INICIAR LEITURAS", 
                        on_click=lambda _: mostrar_leitura_individual(),
                        width=300, height=50, bgcolor=NAVY_BLUE, color="white"
                    ),
                    ft.ElevatedButton(
                        "GERAR RELATÓRIO PDF", 
                        on_click=enviar_relatorio_final,
                        width=300, height=50, bgcolor="white", color=NAVY_BLUE
                    ),
                ], horizontal_alignment="center", spacing=30),
                padding=50
            )
        )
        page.update()

    mostrar_inicio()

if __name__ == "__main__":
    db.init_db()
    ft.app(target=main)
    