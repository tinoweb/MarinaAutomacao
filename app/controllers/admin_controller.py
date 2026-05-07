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
        
        # Verificação simples de credenciais (em produção, use algo mais seguro)
        if username == 'admin' and password == 'senha123':
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
    if request.method == 'POST':
        # Aqui você implementaria a lógica para salvar as configurações
        flash('Configurações salvas com sucesso', 'success')
        return redirect(url_for('admin.settings'))
    
    return render_template('admin/settings.html')

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
