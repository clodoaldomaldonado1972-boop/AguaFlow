import urllib.parse
import flet as ft

def enviar_alerta_whatsapp(page, mensagem):
    # Substitua pelo número do escritório/suporte (com DDD)
    telefone = "5518981337316" 
    texto_url = urllib.parse.quote(mensagem)
    link = f"https://wa.me/{telefone}?text={texto_url}"
    page.launch_url(link)
