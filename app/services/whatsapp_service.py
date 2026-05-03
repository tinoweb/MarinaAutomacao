import os
import requests
from app.models.whatsapp_model import WhatsAppConfig


class WhatsAppAPIService:
    """
    Serviço de comunicação com o WPP Connect Server via REST API.
    O servidor WPP Connect roda como container Docker separado (:21465)
    e gerencia a sessão/QR code do WhatsApp Web.
    """

    def __init__(self):
        self.server_url = os.getenv('WPP_SERVER_URL', 'http://wppconnect:21465')
        self.secret_key = os.getenv('WPP_SECRET_KEY', 'marina_bot_secret')
        self.session_name = os.getenv('WHATSAPP_SESSION', 'marina_bot_session')
        self.app_url = os.getenv('APP_URL', 'http://app:5000')
        self._token = None

    def _get_token(self):
        """Retorna o token armazenado (memória ou banco de dados)."""
        if self._token:
            return self._token
        config = WhatsAppConfig.get_config(self.session_name)
        if config and config.get('token'):
            self._token = config['token']
        return self._token

    def _headers(self):
        """Monta os headers de autenticação para a API do WPP Connect."""
        token = self._get_token()
        if not token:
            return {}
        return {'Authorization': f'Bearer {token}'}

    def generate_token(self, session_name=None):
        """Gera um token de acesso para a sessão no WPP Connect Server."""
        session = session_name or self.session_name
        url = f"{self.server_url}/api/{session}/{self.secret_key}/generate-token"
        try:
            resp = requests.post(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            token = data.get('token')
            if token:
                self._token = token
                WhatsAppConfig.save_config(
                    session_name=session,
                    token=token,
                    status='token_generated'
                )
                print(f"[WPP] Token gerado para sessão '{session}'")
            return token
        except Exception as e:
            print(f"[WPP] Erro ao gerar token: {e}")
            return None

    def start_session(self, session_name=None):
        """Inicia a sessão no WPP Connect Server com webhook apontando para o Flask."""
        session = session_name or self.session_name
        if not self._get_token():
            self.generate_token(session)

        webhook_url = f"{self.app_url}/webhook/wppconnect"
        url = f"{self.server_url}/api/{session}/start-session"
        payload = {
            "webhook": webhook_url,
            "waitForLogin": False,
            "autoClose": 60
        }
        try:
            resp = requests.post(url, json=payload, headers=self._headers(), timeout=30)
            data = resp.json()
            print(f"[WPP] start-session resposta: {data}")
            WhatsAppConfig.save_config(session_name=session, status='starting')
            return data
        except Exception as e:
            print(f"[WPP] Erro ao iniciar sessão: {e}")
            return None

    def get_qrcode(self, session_name=None):
        """Retorna o QR code da sessão em formato base64."""
        session = session_name or self.session_name
        url = f"{self.server_url}/api/{session}/qrcode-session"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                return data.get('qrcode') or data.get('base64Qrcode')
            return None
        except Exception as e:
            print(f"[WPP] Erro ao obter QR code: {e}")
            return None

    def get_status(self, session_name=None):
        """Retorna o status atual da sessão no servidor WPP Connect."""
        session = session_name or self.session_name
        url = f"{self.server_url}/api/{session}/status-session"
        try:
            resp = requests.get(url, headers=self._headers(), timeout=10)
            if resp.status_code == 200:
                return resp.json()
            return {'status': 'error', 'message': f'HTTP {resp.status_code}'}
        except requests.exceptions.ConnectionError:
            return {'status': 'unreachable', 'message': 'Servidor WPP Connect indisponível'}
        except Exception as e:
            print(f"[WPP] Erro ao verificar status: {e}")
            return {'status': 'error', 'message': str(e)}

    def close_session(self, session_name=None):
        """Encerra a sessão e limpa o token."""
        session = session_name or self.session_name
        url = f"{self.server_url}/api/{session}/close-session"
        try:
            resp = requests.post(url, headers=self._headers(), timeout=15)
            data = resp.json()
            WhatsAppConfig.save_config(session_name=session, status='disconnected', token='')
            self._token = None
            print(f"[WPP] Sessão '{session}' encerrada")
            return data
        except Exception as e:
            print(f"[WPP] Erro ao fechar sessão: {e}")
            return None

    def send_message(self, phone, message, session_name=None):
        """Envia uma mensagem de texto para um número via WPP Connect."""
        session = session_name or self.session_name
        url = f"{self.server_url}/api/{session}/send-message"
        payload = {
            "phone": phone,
            "message": message,
            "isGroup": False
        }
        try:
            resp = requests.post(url, json=payload, headers=self._headers(), timeout=15)
            return resp.json()
        except Exception as e:
            print(f"[WPP] Erro ao enviar mensagem: {e}")
            return None

    def logout_session(self, session_name=None):
        """Faz logout da sessão (desvincula o dispositivo)."""
        session = session_name or self.session_name
        url = f"{self.server_url}/api/{session}/logout-session"
        try:
            resp = requests.post(url, headers=self._headers(), timeout=15)
            WhatsAppConfig.save_config(session_name=session, status='disconnected', token='')
            self._token = None
            return resp.json()
        except Exception as e:
            print(f"[WPP] Erro ao fazer logout: {e}")
            return None


_wpp_service = None


def get_wpp_service():
    """Retorna a instância global do serviço WPP Connect."""
    global _wpp_service
    if _wpp_service is None:
        _wpp_service = WhatsAppAPIService()
    return _wpp_service
