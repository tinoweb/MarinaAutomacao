import os
import openai
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

# Configura a API key da OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_ai_response(chat_session):
    """
    Obtém uma resposta da IA com base no histórico da conversa
    
    Args:
        chat_session (ChatSession): Sessão de chat atual
        
    Returns:
        str: Resposta gerada pela IA
    """
    try:
        # Obtém o histórico de conversa formatado
        messages = chat_session.get_conversation_history()
        
        # Verifica se é a primeira mensagem do usuário
        if len(chat_session.messages) == 1:
            # Adiciona uma mensagem de boas-vindas
            return "Olá! Sou o JusBot, assistente virtual especializado em direito trabalhista. Como posso ajudar você hoje? Para começar, poderia me informar seu nome completo?"
        
        # Verifica se já temos o nome do usuário
        if len(chat_session.messages) == 3 and "nome" not in chat_session.user_data:
            # Salva o nome do usuário
            user_name = chat_session.messages[2]["content"]
            chat_session.update_user_data("nome", user_name)
            chat_session.save()
            
            # Pede mais informações
            return f"Obrigado, {user_name}. Para que eu possa entender melhor sua situação, poderia me contar qual problema você está enfrentando com seu empregador?"
        
        # Faz a chamada para a API da OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        # Extrai a resposta
        ai_response = response.choices[0].message.content
        
        # Verifica se a resposta contém informações que precisamos coletar
        _update_user_data_from_response(chat_session, ai_response)
        
        return ai_response
        
    except Exception as e:
        print(f"Erro ao obter resposta da IA: {e}")
        return "Desculpe, estou enfrentando alguns problemas técnicos. Poderia tentar novamente mais tarde ou entrar em contato diretamente com nosso escritório?"

def _update_user_data_from_response(chat_session, response):
    """
    Extrai e atualiza dados do usuário a partir da resposta da IA
    
    Args:
        chat_session (ChatSession): Sessão de chat atual
        response (str): Resposta da IA
    """
    # Aqui você pode implementar lógica para extrair informações importantes
    # da resposta ou da mensagem do usuário, como datas, valores, etc.
    
    # Exemplo: Detectar menção a data de admissão
    if "data de admissão" in response.lower() and "data_admissao" not in chat_session.user_data:
        # Na próxima mensagem do usuário, podemos tentar extrair a data
        chat_session.update_user_data("esperando_data_admissao", True)
    
    # Exemplo: Detectar menção a salário
    if "salário" in response.lower() and "salario" not in chat_session.user_data:
        # Na próxima mensagem do usuário, podemos tentar extrair o salário
        chat_session.update_user_data("esperando_salario", True)
