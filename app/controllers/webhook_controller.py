from flask import Blueprint, request, jsonify
from app.models.chat_model import ChatSession
from app.models.ai_model import get_ai_response

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/webhook', methods=['POST'])
def receive_message():
    """
    Endpoint generico para receber mensagens (legado Twilio - desativado).
    O bot WhatsApp agora usa WPP-Whatsapp diretamente.
    """
    return jsonify({"status": "deprecated", "message": "Use WPP-Whatsapp"})

@webhook_bp.route('/webhook/status', methods=['POST'])
def message_status():
    return jsonify({"status": "received"})
