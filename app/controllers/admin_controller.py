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
    # Aqui você implementaria a lógica para buscar conversas do banco de dados
    conversations = []  # Placeholder para dados reais
    return render_template('admin/conversations.html', conversations=conversations)

@admin_bp.route('/conversas/<conversation_id>')
@login_required
def view_conversation(conversation_id):
    """Visualiza uma conversa específica"""
    # Aqui você implementaria a lógica para buscar uma conversa específica
    conversation = {}  # Placeholder para dados reais
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
