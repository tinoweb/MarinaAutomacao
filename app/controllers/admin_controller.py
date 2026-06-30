from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
import os

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Função para verificar se o usuário está autenticado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login do painel administrativo"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Credenciais lidas das variáveis de ambiente (ADMIN_USER / ADMIN_PASSWORD)
        admin_user = os.getenv('ADMIN_USER', 'admin')
        admin_pass = os.getenv('ADMIN_PASSWORD', 'senha123')
        if username == admin_user and password == admin_pass:
            session['admin_logged_in'] = True
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Credenciais inválidas', 'danger')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    """Rota para logout"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@login_required
def dashboard():
    """Dashboard principal do painel administrativo"""
    return render_template('admin/dashboard.html')

@admin_bp.route('/conversas')
@login_required
def conversations():
    """Lista de conversas ativas e concluídas"""
    from app.models.chat_model import ChatSession
    conversations = ChatSession.get_all_sessions()
    return render_template('admin/conversations.html', conversations=conversations)

@admin_bp.route('/conversas/<conversation_id>')
@login_required
def view_conversation(conversation_id):
    """Visualiza uma conversa específica"""
    from app.models.chat_model import ChatSession
    conversation = ChatSession.get_session(conversation_id)
    if not conversation:
        flash('Conversa não encontrada', 'error')
        return redirect(url_for('admin.conversations'))
    
    return render_template('admin/conversation_detail.html', conversation=conversation)

@admin_bp.route('/configuracoes', methods=['GET', 'POST'])
@login_required
def settings():
    """Configurações do sistema"""
    from app.config.database import get_db_connection

    # Configurações padrão
    defaults = {
        'bot_name': 'AtendBot',
        'welcome_message': 'Olá! Sou o AtendBot, seu assistente virtual. Como posso te ajudar hoje?',
        'system_prompt': '',
        'ai_model': 'gpt-3.5-turbo',
        'temperature': '0.7',
        'whatsapp_number': '',
        'session_name': 'marina_bot_session'
    }

    if request.method == 'POST':
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Chaves que serão salvas
            settings_to_save = [
                'bot_name',
                'welcome_message',
                'system_prompt',
                'ai_model',
                'temperature',
                'session_name'
            ]

            for key in settings_to_save:
                value = request.form.get(key, defaults[key])
                cursor.execute('''
                    INSERT INTO ai_settings (setting_key, setting_value)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE setting_value = %s, updated_at = NOW()
                ''', (key, value, value))

            conn.commit()
            cursor.close()
            conn.close()
            flash('Configurações salvas com sucesso', 'success')
        except Exception as e:
            print(f"[Settings] Erro ao salvar configurações: {e}")
            flash('Erro ao salvar as configurações', 'danger')
        
        return redirect(url_for('admin.settings'))

    # Caso GET: carregar do banco de dados
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT setting_key, setting_value FROM ai_settings")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        for row in rows:
            defaults[row['setting_key']] = row['setting_value']
    except Exception as e:
        print(f"[Settings] Erro ao carregar configurações: {e}")

    # Carrega configurações do WhatsApp
    try:
        from app.models.whatsapp_model import WhatsAppConfig
        wa_config = WhatsAppConfig.get_config()
        if wa_config:
            defaults['whatsapp_number'] = wa_config.get('phone_number', '')
            defaults['session_name'] = wa_config.get('session_name', 'marina_bot_session')
    except Exception as e:
        pass

    return render_template('admin/settings.html', **defaults)

@admin_bp.route('/clientes')
@login_required
def clients():
    """Página de gestão de clientes"""
    from app.models.chat_model import ChatSession
    conversations = ChatSession.get_all_sessions()
    clients_data = []
    for conv in conversations:
        client_info = {
            'id': conv['id'],
            'user_id': conv['user_id'],
            'nome': conv['user_data'].get('name') or conv['user_data'].get('nome') or 'Não informado',
            'email': conv['user_data'].get('email') or 'Não informado',
            'telefone': conv['user_data'].get('real_phone') or conv['user_data'].get('phone') or 'Não definido',
            'motivo_contato': conv['user_data'].get('motivo_contato') or 'Não informado',
            'data_inicio': conv['created_at'].strftime('%d/%m/%Y %H:%M'),
            'ultima_mensagem': conv['updated_at'].strftime('%d/%m/%Y %H:%M'),
            'status': conv['status'],
            'total_mensagens': len(conv.get('messages', [])),
            'dados_completos': bool(conv['user_data'].get('nome') and conv['user_data'].get('email') and conv['user_data'].get('motivo_contato'))
        }
        clients_data.append(client_info)
    clients_data.sort(key=lambda x: x['data_inicio'], reverse=True)
    return render_template('admin/clients.html', clients=clients_data)

@admin_bp.route('/clientes/<int:client_id>')
@login_required
def view_client(client_id):
    """Visualiza detalhes de um cliente específico"""
    from app.models.chat_model import ChatSession
    session_data = ChatSession.get_session(client_id)
    if not session_data:
        flash('Cliente não encontrado', 'error')
        return redirect(url_for('admin.clients'))
    
    return render_template('admin/client_detail.html', client=session_data)
