import os
from app import create_app
from app.services.whatsapp_service import WhatsAppBotService

app = create_app()

if __name__ == '__main__':
    # Inicia o bot do WhatsApp apenas no processo principal (evita duplicar no reloader do Flask)
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        bot = WhatsAppBotService()
        bot.start()

    app.run(host='0.0.0.0', port=5000, debug=True)
