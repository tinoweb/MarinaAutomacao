import os
import mysql.connector
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

def get_db_connection():
    """
    Cria e retorna uma conexão com o banco de dados MySQL
    
    Returns:
        connection: Objeto de conexão com o MySQL
    """
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', ''),
            database=os.getenv('MYSQL_DB', 'jusbot'),
            port=int(os.getenv('MYSQL_PORT', 3306))
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao MySQL: {err}")
        raise

def init_db():
    """
    Inicializa o banco de dados criando as tabelas necessárias se não existirem
    """
    try:
        # Obtém conexão com o banco
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Cria tabela de sessões de chat
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(50) NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'active',
            UNIQUE KEY (user_id)
        )
        ''')
        
        # Cria tabela de mensagens
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id INT NOT NULL,
            role VARCHAR(20) NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
        )
        ''')
        
        # Cria tabela de dados do usuário
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id INT NOT NULL,
            key_name VARCHAR(50) NOT NULL,
            value TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
            UNIQUE KEY (session_id, key_name)
        )
        ''')
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("Banco de dados inicializado com sucesso!")
        
    except mysql.connector.Error as err:
        print(f"Erro ao inicializar o banco de dados: {err}")
        raise
