import os
import threading
from WPP_Whatsapp import Create
from app.models.chat_model import ChatSession
from app.models.ai_model import get_ai_response


class WhatsAppBotService:
    """
    Servico de automacao do WhatsApp usando WPP-Whatsapp (API nao oficial).
    Roda em uma thread separada para nao bloquear o servidor Flask.
    """

    def __init__(self, session_name=None):
        self.session_name = session_name or os.getenv("WHATSAPP_SESSION", "marina_bot")
        self.client = None
        self.thread = None
        self.running = False

    def _on_message(self, message):
        """Handler chamado quando uma mensagem e recebida."""
        # Ignora mensagens de grupo
        if message.get("isGroupMsg"):
            return

        sender_id = message.get("from", "")
        incoming_msg = message.get("body", "").strip()

        if not incoming_msg or not sender_id:
            return

        print(f"[WhatsApp] Mensagem de {sender_id}: {incoming_msg}")

        try:
            chat_session = ChatSession(sender_id)
            chat_session.add_message("user", incoming_msg)

            ai_response = get_ai_response(chat_session)

            chat_session.add_message("assistant", ai_response)
            chat_session.save()

            if self.client:
                self.client.sendText(sender_id, ai_response)
                print(f"[WhatsApp] Resposta enviada para {sender_id}")
        except Exception as e:
            print(f"[WhatsApp] Erro ao processar mensagem: {e}")
            if self.client:
                try:
                    self.client.sendText(
                        sender_id,
                        "Desculpe, ocorreu um erro ao processar sua mensagem. Tente novamente mais tarde."
                    )
                except Exception:
                    pass

    def _run_bot(self):
        """Loop principal do bot (bloqueante)."""
        try:
            print(f"[WhatsApp] Iniciando sessao '{self.session_name}'...")
            creator = Create(session=self.session_name)
            self.client = creator.start()

            self.client.on_message(self._on_message)

            print("[WhatsApp] Bot iniciado! Escaneie o QR code se solicitado.")
            self.client.start()

        except Exception as e:
            print(f"[WhatsApp] Erro fatal no bot: {e}")
        finally:
            self.running = False
            print("[WhatsApp] Bot encerrado.")

    def start(self):
        """Inicia o bot em uma thread daemon."""
        if self.running:
            print("[WhatsApp] Bot ja esta rodando.")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_bot, daemon=True)
        self.thread.start()
        print("[WhatsApp] Thread do bot iniciada.")

    def stop(self):
        """Para o bot de forma controlada."""
        self.running = False
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
