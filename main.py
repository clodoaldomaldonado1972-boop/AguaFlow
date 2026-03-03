import flet as ft
# Importe o arquivo database no topo do main.py
import database 

# ... dentro da função btn_proximo_click:
def btn_proximo_click(e):
    # (Suas validações já existentes aqui)
    
    # COMANDO PARA SALVAR:
    database.salvar_leitura(
        unidade=unidades[indice[0]],
        agua=input_agua.value,
        gas=input_gas.value
    )
    
    # (Restante da sua lógica de avançar unidade...)

def main(page: ft.Page):
    page.title = "AguaFlow - Gestão Condominial"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 20
    
    unidades = ["Hidrômetro Geral", "Área de Lazer", "Apto 166", "Apto 165", "Apto 164"]
    indice = [0] 

    txt_unidade_atual = ft.Text(f"Unidade Atual: {unidades[0]}", size=20, weight="bold", color="blue700")
    
    # Ícones corrigidos para compatibilidade
    input_agua = ft.TextField(label="Hidrômetro de Água (m³)", icon=ft.icons.WATER, keyboard_type=ft.KeyboardType.NUMBER)
    input_gas = ft.TextField(label="Medidor de Gás (m³)", icon=ft.icons.OPACITY, keyboard_type=ft.KeyboardType.NUMBER)

    def btn_proximo_click(e):
        if not input_agua.value:
            input_agua.error_text = "Campo obrigatório"
            page.update()
            return
        
        # Lógica de avançar...
        if indice[0] < len(unidades) - 1:
            indice[0] += 1
            txt_unidade_atual.value = f"Unidade Atual: {unidades[indice[0]]}"
            input_agua.value = ""
            input_gas.value = ""
        page.update()

    btn_salvar = ft.ElevatedButton("Salvar e Próximo", on_click=btn_proximo_click, bgcolor="blue900", color="white")
    
    page.add(txt_unidade_atual, input_agua, input_gas, btn_salvar)

# Use ft.app se estiver em versões antigas, ou apenas mude os ícones primeiro
ft.app(target=main)