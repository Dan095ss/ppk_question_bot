import sqlite3

def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect('questions.db')
    c = conn.cursor()

    # Таблица категорий
    c.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')

    # Таблица вопросов и ответов
    c.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER,
            question TEXT NOT NULL,
            answer TEXT,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')

    # Таблица администраторов
    c.execute('''
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY
        )
    ''')

    conn.commit()
    conn.close()


def add_category(name):
    """Добавление категории в базу данных"""
    conn = sqlite3.connect('questions.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO categories (name) VALUES (?)', (name,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Категория уже существует
    finally:
        conn.close()


def get_categories():
    """Получение списка всех категорий"""
    conn = sqlite3.connect('questions.db')
    c = conn.cursor()
    c.execute('SELECT name FROM categories')
    categories = [row[0] for row in c.fetchall()]
    conn.close()
    return categories


def add_question(category_name, question, answer=None):
    """Добавление вопроса и ответа в указанную категорию"""
    conn = sqlite3.connect('questions.db')
    c = conn.cursor()
    c.execute('SELECT id FROM categories WHERE name = ?', (category_name,))
    category_id = c.fetchone()
    if category_id:
        c.execute('INSERT INTO questions (category_id, question, answer) VALUES (?, ?, ?)', (category_id[0], question, answer))
        conn.commit()
    conn.close()


def update_answer(category_name, question, answer):
    """Обновление ответа на вопрос"""
    conn = sqlite3.connect('questions.db')
    c = conn.cursor()
    c.execute('''
        UPDATE questions
        SET answer = ?
        WHERE category_id = (SELECT id FROM categories WHERE name = ?)
        AND question = ?
    ''', (answer, category_name, question))
    conn.commit()
    conn.close()


def get_questions_by_category(category_name):
    """Получение списка вопросов и ответов по категории"""
    conn = sqlite3.connect('questions.db')
    c = conn.cursor()
    c.execute('''
        SELECT q.question, q.answer 
        FROM questions q
        JOIN categories c ON q.category_id = c.id
        WHERE c.name = ?
    ''', (category_name,))
    questions = [{'вопрос': row[0], 'ответ': row[1]} for row in c.fetchall()]
    conn.close()
    return questions


def add_admin(admin_id):
    """Добавление администратора в базу данных"""
    conn = sqlite3.connect('questions.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO admins (id) VALUES (?)', (admin_id,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Администратор уже существует
    finally:
        conn.close()


def is_admin(admin_id):
    """Проверка, является ли пользователь администратором"""
    conn = sqlite3.connect('questions.db')
    c = conn.cursor()
    c.execute('SELECT id FROM admins WHERE id = ?', (admin_id,))
    result = c.fetchone()
    conn.close()
    return result is not None