from flask import Blueprint, request, jsonify
from app.models.chat_model import ChatSession
from app.models.ai_model import get_ai_response
from app.models.whatsapp_model import WhatsAppConfig

webhook_bp = Blueprint('webhook', __name__)


@webhook_bp.route('/webhook/wppconnect', methods=['POST'])
def wppconnect_webhook():
    """Recebe todos os eventos enviados pelo WPP Connect Server."""
    data = request.get_json(silent=True) or {}
    event = data.get('event', '')
    session = data.get('session', '')

    if event == 'onConnected':
        phone = data.get('phone', '')
        WhatsAppConfig.save_config(
            session_name=session,
            phone_number=phone,
            status='connected'
        )
        print(f"[Webhook] Sessão '{session}' conectada. Telefone: {phone}")
        return jsonify({'status': 'ok'})

    if event in ('onDisconnected', 'qrReadFail', 'sessionExpired', 'browserClose'):
        WhatsAppConfig.save_config(session_name=session, status='disconnected')
        print(f"[Webhook] Sessão '{session}' desconectada. Evento: {event}")
        return jsonify({'status': 'ok'})

    if event == 'onmessage':
        message = data.get('message', {})
        _handle_incoming_message(session, message)
        return jsonify({'status': 'ok'})

    return jsonify({'status': 'ignored', 'event': event})


def _handle_incoming_message(session, message):
    """Processa mensagem recebida e responde com IA via WPP Connect."""
    if message.get('isGroupMsg') or message.get('fromMe'):
        return

    sender_id = message.get('from', '')
    text = message.get('body', '').strip()

    if not text or not sender_id:
        return

    print(f"[Webhook] Mensagem de {sender_id}: {text}")

    try:
        from app.services.whatsapp_service import get_wpp_service

        chat_session = ChatSession(sender_id)
        chat_session.add_message('user', text)

        ai_response = get_ai_response(chat_session)

        chat_session.add_message('assistant', ai_response)
        chat_session.save()

        wpp = get_wpp_service()
        wpp.send_message(sender_id, ai_response, session_name=session)
        print(f"[Webhook] Resposta enviada para {sender_id}")

    except Exception as e:
        print(f"[Webhook] Erro ao processar mensagem de {sender_id}: {e}")
