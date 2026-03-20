"""
================================================================================
📱 PASTA: views/ - "VITRINE" DO AGUAFLOW
================================================================================

Esta pasta contém toda a interface do usuário (UI) com Flet.
É a nossa "VITRINE" onde o zelador do Vivere Prudente insere as leituras.

🎨 POR QUE "VITRINE"?
   - É onde o usuário interage com o sistema
   - Interface amigável e intuitiva (campo grande, botões claros)
   - Feedback visual em tempo real (cores verde/vermelha)
   - Validação while-you-type (avisa antes de salvar)
   - Sequenciamento automático (16→1, não deixa confundir)
   - Telas incríveis para usar no celular em campo

📦 MÓDULOS PRINCIPAIS:
   • medicao.py       → Tela sequencial de medição (VITRINE MAIN!)
   • auth.py          → Autenticação de usuários
   • reports.py       → Relatórios mensais em PDF
   • utils.py         → Utilitários (email, helpers)
   • estilos.py       → Temas e estilos visuais

🛠️ UTILITÁRIOS DE INTEGRAÇÃO:
   • camera_utils.py    → Integração com câmera do celular
   • leitor_ocr.py      → Reconhecimento óptico de caracteres
   • gerador_qr.py      → Gerador de QR codes para etiquetas
   • gerador_pdf.py     → Geração de PDFs
   • audio_utils.py     → Suporte para áudio/notificações
   • ligar_celular.py   → Integração com ligações telefônicas

🧪 MÓDULOS DE TESTE:
   • teste.py, teste_email.py, teste_local.py, etc.
   → Para desenvolvimento e debug

✨ CARACTERÍSTICAS DA VITRINE:
   ✓ Interface responsiva (funciona em qualquer celular)
   ✓ Validação em tempo real (sem erros)
   ✓ Feedback visual claro (ícones, cores, mensagens)
   ✓ Sem perda de dados (integrada com o "cofre local")
   ✓ Pronta para offline (tudo funciona sem Wi-Fi)

Por trás da cenotapéia "VITRINE", tudo está conectado ao "COFRE LOCAL" 
(database/) que garante que nenhum dado se perca.

================================================================================
"""

# Exports principais para facilitar import
from views.medicao import montar_tela

__all__ = ['montar_tela']
