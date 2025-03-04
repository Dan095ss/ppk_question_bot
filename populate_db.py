import sqlite3
from database import add_category, add_question, add_admin

# Подключение к базе данных
conn = sqlite3.connect('questions.db')
c = conn.cursor()

# Тестовые данные
test_data = [
    {
        "category": "Категория 1",
        "questions": [
            {"вопрос": "Что такое госслужба?", "ответ": "Государственная служба - это..."},
            {"вопрос": "Как стать госслужащим?", "ответ": "Для того чтобы стать госслужащим..."}
        ]
    },
    {
        "category": "Категория 2",
        "questions": [
            {"вопрос": "Какие документы нужны для приема на госслужбу?", "ответ": "Для приема на госслужбу нужны..."},
            {"вопрос": "Какие права имеет госслужащий?", "ответ": "Госслужащий имеет право..."}
        ]
    }
]

# Добавление категорий и вопросов
for category_data in test_data:
    category_name = category_data["category"]

    # Добавляем категорию
    try:
        add_category(category_name)
    except Exception as e:
        print(f"Ошибка при добавлении категории '{category_name}': {e}")

    # Добавляем вопросы и ответы
    for question_data in category_data["questions"]:
        question = question_data["вопрос"]
        answer = question_data["ответ"]
        try:
            add_question(category_name, question, answer)
        except Exception as e:
            print(f"Ошибка при добавлении вопроса '{question}' в категорию '{category_name}': {e}")

# Добавляем администратора
add_admin(498613988)  # Ваш ID администратора

print("Тестовые данные успешно добавлены в базу данных!")