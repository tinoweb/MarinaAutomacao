import os
import re
from openai import OpenAI
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# Instancia o cliente OpenAI
_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_system_prompt():
    """
    Carrega o prompt de personalidade do arquivo personalidade.txt
    """
    try:
        # personalidade.txt está na raiz do projeto (dois níveis acima de app/models)
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        prompt_path = os.path.join(base_dir, 'personalidade.txt')
        if os.path.exists(prompt_path):
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        print(f"Erro ao carregar personalidade.txt: {e}")
    
    # Fallback padrão caso o arquivo não exista ou dê erro
    return (
        "Você é Camila, assistente virtual da Dra. Marina Marques, advogada especialista em Direito Previdenciário. "
        "Seu objetivo é realizar atendimento inicial, qualificar leads, identificar oportunidades e coletar informações. "
        "Seja cordial, empática, objetiva e profissional. Faça apenas uma pergunta por vez de forma curta."
    )

def get_ai_response(chat_session):
    """
    Obtém uma resposta da IA com base no histórico da conversa
    
    Args:
        chat_session (ChatSession): Sessão de chat atual
        
    Returns:
        str: Resposta gerada pela IA
    """
    try:
        # Analisa a conversa para tentar extrair dados do lead antes de chamar a IA
        _update_user_data_from_conversation(chat_session)

        # Obtém o histórico de conversa formatado
        messages = chat_session.get_conversation_history()
        
        # Faz a chamada para a API da OpenAI
        response = _client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        # Extrai a resposta
        ai_response = response.choices[0].message.content
        
        # Verifica se a resposta contém informações que precisamos coletar
        _update_user_data_from_response(chat_session, ai_response)
        
        # Roda a extração novamente após a nova resposta da IA
        _update_user_data_from_conversation(chat_session)

        return ai_response
        
    except Exception as e:
        print(f"Erro ao obter resposta da IA: {e}")
        return "Desculpe, estou enfrentando alguns problemas técnicos no momento. Poderia tentar novamente mais tarde?"

def _update_user_data_from_conversation(chat_session):
    """
    Analisa as mensagens trocadas na conversa para tentar extrair nome, email, telefone e benefício de interesse.
    """
    messages = chat_session.messages
    if not messages:
        return

    # Salva o telefone real a partir do user_id se não estiver preenchido
    if 'real_phone' not in chat_session.user_data:
        clean_phone = chat_session.user_id.split('@')[0]
        chat_session.update_user_data('real_phone', clean_phone)

    # Varre as mensagens do usuário e da IA para extrair informações do lead
    for i in range(len(messages) - 1):
        msg_ai = messages[i]
        msg_user = messages[i+1]

        if msg_ai['role'] == 'assistant' and msg_user['role'] == 'user':
            ai_content = msg_ai['content'].lower()
            user_content = msg_user['content'].strip()

            # Extração de Nome
            if 'nome' not in chat_session.user_data:
                # Se a IA perguntou o nome na mensagem anterior
                if any(q in ai_content for q in ['seu nome', 'como se chama', 'quem fala', 'me informe seu nome', 'qual é o seu nome', 'poderia me dizer seu nome']):
                    name = user_content
                    # Remove prefixos comuns de apresentação
                    for prefix in ['meu nome é', 'meu nome e', 'eu sou a', 'eu sou o', 'sou a', 'sou o', 'me chamo']:
                        if name.lower().startswith(prefix):
                            name = name[len(prefix):].strip()
                    # Salva se o nome for razoável
                    if 0 < len(name) < 50:
                        chat_session.update_user_data('nome', name)

            # Extração de Email
            if 'email' not in chat_session.user_data:
                email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', user_content)
                if email_match:
                    chat_session.update_user_data('email', email_match.group(0))

            # Extração de Telefone
            if 'telefone' not in chat_session.user_data:
                phone_match = re.search(r'(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?\d{4,5}-?\d{4}', user_content)
                if phone_match:
                    chat_session.update_user_data('telefone', phone_match.group(0))

            # Extração de Motivo do Contato (Benefício de interesse)
            if 'motivo_contato' not in chat_session.user_data:
                benefits = [
                    'salário maternidade', 'salario maternidade', 'aposentadoria', 'bpc', 'loas', 
                    'auxílio-doença', 'auxilio-doenca', 'auxílio doença', 'auxilio doenca',
                    'pensão por morte', 'pensao por morte', 'benefício negado', 'beneficio negado', 
                    'planejamento previdenciário', 'planejamento previdenciario', 'benefício rural', 
                    'beneficio rural', 'revisão', 'revisao', 'recurso', 'auxílio-reclusão', 
                    'auxilio-reclusao', 'auxílio-acidente', 'auxilio-acidente', 'aposentadoria rural',
                    'auxílio por incapacidade', 'auxilio por incapacidade'
                ]
                for benefit in benefits:
                    if benefit in user_content.lower():
                        chat_session.update_user_data('motivo_contato', benefit.title())
                        break

def _update_user_data_from_response(chat_session, response):
    """
    Extrai e atualiza dados do usuário a partir da resposta da IA
    
    Args:
        chat_session (ChatSession): Sessão de chat atual
        response (str): Resposta da IA
    """
    # Exemplo: Detectar menção a data de admissão
    if "data de admissão" in response.lower() and "data_admissao" not in chat_session.user_data:
        # Na próxima mensagem do usuário, podemos tentar extrair a data
        chat_session.update_user_data("esperando_data_admissao", True)
    
    # Exemplo: Detectar menção a salário
    if "salário" in response.lower() and "salario" not in chat_session.user_data:
        # Na próxima mensagem do usuário, podemos tentar extrair o salário
        chat_session.update_user_data("esperando_salario", True)
