import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackContext,
    ConversationHandler,
    MessageHandler,
    filters
)

# Импортируем функции работы с БД
from database import init_db, add_category, get_categories, add_question, update_answer, get_questions_by_category, add_admin, is_admin

# Настройка логирования (в файл и консоль)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot_log.log', mode='a', encoding='utf-8'),  # Логирование в файл
        logging.StreamHandler()  # Логирование в консоль
    ]
)
logger = logging.getLogger(__name__)


# Состояния для диалога администратора
ADD_CATEGORY, ADD_QUESTION, ADD_ANSWER = range(3)


# Функция для динамической генерации клавиатуры категорий
def generate_category_keyboard():
    categories = get_categories()
    logger.debug(f"Список категорий: {categories}")
    CATEGORY_KEYBOARD = [[cat] for cat in categories] + [["Назад"]]
    return ReplyKeyboardMarkup(CATEGORY_KEYBOARD, resize_keyboard=True)


# Обработчик команды /start
async def start(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    logger.info(f"Пользователь [{user.id}] ({user.first_name} {user.last_name or ''}) начал работу с ботом.")
    keyboard = generate_category_keyboard()
    await update.message.reply_text(
        "Добро пожаловать в справочник госслужащего! Выберите категорию:",
        reply_markup=keyboard
    )


# Обработчик выбора категории
async def category_handler(update: Update, context: CallbackContext) -> None:
    input_text = update.message.text.strip()
    user = update.message.from_user  # Получаем информацию о пользователе
    logger.debug(f"Пользователь [{user.id}] ({user.first_name} {user.last_name or ''}) выбрал: {input_text}")

    # Если введено число и категория уже выбрана - это номер вопроса
    if input_text.isdigit() and context.user_data.get("current_category"):
        logger.info(f"Пользователь [{user.id}] ({user.first_name} {user.last_name or ''}) пытается выбрать вопрос.")
        await question_handler(update, context)
        return

    if input_text == "Назад":
        logger.info(f"Пользователь [{user.id}] ({user.first_name} {user.last_name or ''}) вернулся к списку категорий.")
        await back_to_categories(update, context)
        return

    questions = get_questions_by_category(input_text)

    if not questions:
        logger.warning(f"Категория '{input_text}' не существует или не содержит вопросов. Пользователь [{user.id}] ({user.first_name} {user.last_name or ''}).")
        await update.message.reply_text(
            "Такой категории не существует. Попробуйте снова.",
            reply_markup=generate_category_keyboard()
        )
        return

    questions_list = "\n".join([f"{i+1}. {q['вопрос']}" for i, q in enumerate(questions)])
    keyboard = ReplyKeyboardMarkup([[f"{i+1}"] for i in range(len(questions))] + [["Назад"]], resize_keyboard=True)

    # Логируем успешный выбор категории
    logger.info(f"Пользователь [{user.id}] ({user.first_name} {user.last_name or ''}) успешно выбрал категорию '{input_text}'.")
    await update.message.reply_text(
        f"В категории '{input_text}' есть следующие вопросы:\n{questions_list}\nВыберите номер вопроса или нажмите 'Назад' для возврата.",
        reply_markup=keyboard
    )

    # Сохраняем текущую категорию в user_data
    context.user_data["current_category"] = input_text


# Обработчик выбора вопроса
async def question_handler(update: Update, context: CallbackContext) -> None:
    try:
        category = context.user_data.get("current_category")
        user = update.message.from_user  # Получаем информацию о пользователе
        logger.debug(f"Текущая категория: {category}")

        if not category:
            logger.error(f"Ошибка: Не выбрана категория. Пользователь [{user.id}] ({user.first_name} {user.last_name or ''}).")
            await update.message.reply_text(
                "Сначала выберите категорию.",
                reply_markup=generate_category_keyboard()
            )
            return

        try:
            question_index = int(update.message.text.strip()) - 1
            logger.debug(f"Преобразован номер вопроса: {question_index}")
        except ValueError:
            logger.error(f"Ошибка: Введено некорректное значение вместо номера вопроса. Пользователь [{user.id}] ({user.first_name} {user.last_name or ''}).")
            await update.message.reply_text(
                "Пожалуйста, введите номер вопроса (число).",
                reply_markup=generate_category_keyboard()
            )
            return

        questions = get_questions_by_category(category)

        if not questions:
            logger.error(f"Ошибка: В категории '{category}' нет вопросов. Пользователь [{user.id}] ({user.first_name} {user.last_name or ''}).")
            await update.message.reply_text(
                "В данной категории нет вопросов.",
                reply_markup=generate_category_keyboard()
            )
            return

        if question_index < 0 or question_index >= len(questions):
            logger.error(f"Ошибка: Неверный номер вопроса ({question_index}). Пользователь [{user.id}] ({user.first_name} {user.last_name or ''}).")
            await update.message.reply_text(
                "Неверный номер вопроса. Попробуйте снова.",
                reply_markup=generate_category_keyboard()
            )
            return

        question = questions[question_index]['вопрос']
        answer = questions[question_index].get('ответ', 'Ответ отсутствует.')

        # Логируем успешный выбор вопроса
        logger.info(f"Пользователь [{user.id}] ({user.first_name} {user.last_name or ''}) выбрал вопрос '{question}' из категории '{category}'.")
        await update.message.reply_text(
            f"Вопрос: {question}\nОтвет: {answer}"
        )

        # Показываем снова список вопросов для текущей категории
        questions_list = "\n".join([f"{i+1}. {q['вопрос']}" for i, q in enumerate(questions)])
        keyboard = ReplyKeyboardMarkup([[f"{i+1}"] for i in range(len(questions))] + [["Назад"]], resize_keyboard=True)
        await update.message.reply_text(
            f"В категории '{category}' есть следующие вопросы:\n{questions_list}\nВыберите номер вопроса или нажмите 'Назад' для возврата.",
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Произошла ошибка: {e}. Пользователь [{user.id}] ({user.first_name} {user.last_name or ''}).")
        await update.message.reply_text("Произошла ошибка. Попробуйте снова.")


# Возвращение к списку категорий
async def back_to_categories(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    logger.info(f"Пользователь [{user.id}] ({user.first_name} {user.last_name or ''}) вернулся к списку категорий.")
    if "current_category" in context.user_data:
        context.user_data.pop("current_category", None)
        logger.debug(f"Очищено состояние current_category для пользователя [{user.id}] ({user.first_name} {user.last_name or ''}).")
    keyboard = generate_category_keyboard()
    await update.message.reply_text(
        "Вы вернулись к списку категорий.",
        reply_markup=keyboard
    )


# Админ-панель
async def admin_panel(update: Update, context: CallbackContext) -> int:
    user_id = update.message.from_user.id
    user = update.message.from_user
    logger.info(f"Попытка входа в админ-панель от пользователя [{user.id}] ({user.first_name} {user.last_name or ''}).")
    if not is_admin(user_id):  # Проверяем права доступа через БД
        logger.warning(f"Отказано в доступе к админ-панели для пользователя [{user.id}] ({user.first_name} {user.last_name or ''}).")
        await update.message.reply_text(
            "У вас нет прав доступа к админ-панели.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    logger.info(f"Успешный вход в админ-панель для пользователя [{user.id}] ({user.first_name} {user.last_name or ''}).")
    keyboard = ReplyKeyboardMarkup([["/cancel"]], resize_keyboard=True)
    await update.message.reply_text(
        "Добро пожаловать в админ-панель!\nВведите название новой категории или нажмите /cancel для выхода.",
        reply_markup=keyboard
    )
    return ADD_CATEGORY


# Добавление категории
async def add_category_admin(update: Update, context: CallbackContext) -> int:
    category = update.message.text.strip()
    user = update.message.from_user
    if category == "/cancel":
        await cancel(update, context)
        return ConversationHandler.END

    add_category(category)
    context.user_data["current_category"] = category
    logger.info(f"Администратор [{user.id}] ({user.first_name} {user.last_name or ''}) создал категорию '{category}'.")
    await update.message.reply_text(
        f"Категория '{category}' успешно создана.\nВведите вопрос или нажмите /cancel для выхода.",
        reply_markup=ReplyKeyboardMarkup([["/cancel"]], resize_keyboard=True)
    )
    return ADD_QUESTION


# Добавление вопроса
async def add_question_admin(update: Update, context: CallbackContext) -> int:
    question = update.message.text.strip()
    user = update.message.from_user
    if question == "/cancel":
        await cancel(update, context)
        return ConversationHandler.END

    category = context.user_data.get("current_category")
    if not category:
        await update.message.reply_text(
            "Произошла ошибка. Попробуйте начать заново.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    add_question(category, question)
    context.user_data["current_question"] = question
    logger.info(f"Администратор [{user.id}] ({user.first_name} {user.last_name or ''}) добавил вопрос '{question}' в категорию '{category}'.")
    await update.message.reply_text(
        f"Вопрос '{question}' добавлен.\nВведите ответ или нажмите /cancel для выхода.",
        reply_markup=ReplyKeyboardMarkup([["/cancel"]], resize_keyboard=True)
    )
    return ADD_ANSWER


# Добавление ответа
async def add_answer_admin(update: Update, context: CallbackContext) -> int:
    answer = update.message.text.strip()
    user = update.message.from_user
    if answer == "/cancel":
        await cancel(update, context)
        return ConversationHandler.END

    category = context.user_data.get("current_category")
    question = context.user_data.get("current_question")
    if not category or not question:
        await update.message.reply_text(
            "Произошла ошибка. Попробуйте начать заново.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    update_answer(category, question, answer)
    logger.info(f"Администратор [{user.id}] ({user.first_name} {user.last_name or ''}) добавил ответ '{answer}' на вопрос '{question}' в категории '{category}'.")
    await update.message.reply_text(
        f"Ответ '{answer}' успешно добавлен.\nКатегория и вопрос сохранены. Вы можете продолжить добавление.",
        reply_markup=ReplyKeyboardMarkup([["/cancel"]], resize_keyboard=True)
    )
    return ADD_QUESTION


# Отмена операции
async def cancel(update: Update, context: CallbackContext) -> int:
    user = update.message.from_user
    logger.info(f"Пользователь [{user.id}] ({user.first_name} {user.last_name or ''}) отменил операцию.")
    await update.message.reply_text(
        "Операция отменена. Вернитесь в главное меню.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# Обработчик ошибок
async def error_handler(update: object, context: CallbackContext) -> None:
    if isinstance(update, Update) and update.message:
        user = update.message.from_user
        logger.error(f"Ошибка обработки запроса от пользователя [{user.id}] ({user.first_name} {user.last_name or ''}): {context.error}")
        await update.message.reply_text("Произошла ошибка. Попробуйте снова.")


def main() -> None:
    logger.info("Запуск бота...")
    # Инициализация базы данных
    init_db()

    # Добавляем администратора при старте бота
    add_admin(498613988)  # Ваш ID администратора

    application = (
        Application.builder()
        .token("7954046195:AAEbguicLY1C65GGF4GFKpUN-cCQ6Y4kwPM")
        .http_version("1.1")  # Используем HTTP/1.1 для стабильности
        .build()
    )

    # Регистрация обработчика ошибок
    application.add_error_handler(error_handler)

    # Обработчики для админ-панели
    admin_handler = ConversationHandler(
        entry_points=[CommandHandler("admin", admin_panel)],
        states={
            ADD_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_category_admin)],
            ADD_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_question_admin)],
            ADD_ANSWER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_answer_admin)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    application.add_handler(admin_handler)  # Регистрируем админ-панель первым

    # Обработчики для обычных пользователей
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Regex(r"^(Назад)$"), back_to_categories))

    # Обработчик категорий (текстовые сообщения)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, category_handler))

    # Запуск бота
    logger.info("Бот запущен.")
    application.run_polling()


if __name__ == '__main__':
    main()