from flask import Blueprint, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
from app.models.chat_model import ChatSession
from app.models.ai_model import get_ai_response
import os

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/webhook', methods=['POST'])
def receive_message():
    """
    Endpoint para receber mensagens do WhatsApp via Twilio
    """
    # Extrai informações da mensagem recebida
    incoming_msg = request.values.get('Body', '').strip()
    sender_id = request.values.get('From', '')
    
    # Cria ou recupera a sessão de chat para este usuário
    chat_session = ChatSession(sender_id)
    
    # Adiciona a mensagem do usuário ao histórico
    chat_session.add_message("user", incoming_msg)
    
    # Obtém resposta da IA com base no histórico da conversa
    ai_response = get_ai_response(chat_session)
    
    # Adiciona a resposta da IA ao histórico
    chat_session.add_message("assistant", ai_response)
    
    # Salva a sessão atualizada
    chat_session.save()
    
    # Cria resposta para o Twilio
    resp = MessagingResponse()
    resp.message(ai_response)
    
    return str(resp)

@webhook_bp.route('/webhook/status', methods=['POST'])
def message_status():
    """
    Endpoint para receber atualizações de status das mensagens enviadas
    """
    message_sid = request.values.get('MessageSid', '')
    message_status = request.values.get('MessageStatus', '')
    
    # Aqui você pode implementar lógica para lidar com diferentes status
    # como "delivered", "failed", etc.
    
    return jsonify({"status": "received"})
