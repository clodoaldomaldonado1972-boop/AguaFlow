import urllib.parse
import flet as ft

def enviar_alerta_MESSAGE(page: ft.Page, mensagem: str):
    # Número fixo conforme seu código anterior
    contato = "5518981337316" 
    texto_url = urllib.parse.quote(mensagem)
    print(f"DEBUG [Monitoramento]: Enviando alerta para {contato}")
    
    link = f"https://wa.me/{contato}?text={texto_url}"
    if page:
        page.launch_url(link)
    return True