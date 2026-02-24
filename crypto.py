
# ========== INFO ==========
#BOT_TOKEN = '8343325726:AAHEr2lDA95rqXfoJpop4lXDTe2wO_C-9tE'
#WALLET = 'TXZi8mNFMzGmNYKdAaCzE5p3yJaY8JN8QR'
import os
import logging
import qrcode
import telebot
from telebot import types
from io import BytesIO
from datetime import datetime

# ========== ТВОИ АДРЕСА (ВСТАВЬ СВОИ) ==========
BOT_TOKEN = "8343325726:AAHEr2lDA95rqXfoJpop4lXDTe2wO_C-9tE"  # Токен бота

# Адреса кошельков для разных сетей
WALLETS = {
    'TRON': 'TV6TanQXbhsbkP8tSJKCnEcopyXE5aks7j',      # Твой TRX адрес
    'TON': 'UQAywRM74Dsb0V7Icy-5HcnUEKMoQbTOVCTnDm-7PKQohywo',  # Твой TON адрес
    'ETH': '0x5d13eB7CF8f5fe5dbA46fCc71a3c9A4C7eE5fcf8',  # Твой ETH адрес
    'Solana': '2NasfpLqN8tK5TxMH97uJLLZk5hbcFMT89bDeyuJFGVQ',   # USDT обычно на TRON
    'BTC': 'bc1qk8qynpmcrkhtqdgxpjkqrdgvcq4v4xmfqrpy34'    # Твой BTC адрес
}
# ==============================================

# Названия сетей для отображения
NETWORK_NAMES = {
    'TRON': '🌐 TRON (TRX, USDT)',
    'TON': '💎 TON (Toncoin)',
    'ETH': '⚡ Ethereum (ETH, USDT)',
    'Solana': 'Solana (Sol)',
    'BTC': '🪙 Bitcoin (BTC)'
}

# Создаем папку для скриншотов
SCREENSHOTS_DIR = "screenshots"
if not os.path.exists(SCREENSHOTS_DIR):
    os.makedirs(SCREENSHOTS_DIR)

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# Хранилище данных пользователей
user_sessions = {}

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# ========== ФУНКЦИИ ==========

def generate_qr(text):
    """Генерирует QR-код с адресом кошелька"""
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=5
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    bio = BytesIO()
    bio.name = 'qr.png'
    img.save(bio, 'PNG')
    bio.seek(0)
    return bio

def main_keyboard():
    """Основная клавиатура"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('💰 Пополнить', '📋 Сети')
    keyboard.row('❓ Помощь')
    return keyboard

def network_selection_keyboard():
    """Клавиатура выбора сети"""
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for network in WALLETS.keys():
        buttons.append(types.InlineKeyboardButton(
            NETWORK_NAMES[network],
            callback_data=f"net_{network}"
        ))
    keyboard.add(*buttons)
    keyboard.add(types.InlineKeyboardButton("❌ Отмена", callback_data="cancel"))
    return keyboard

# ========== ОБРАБОТЧИКИ КОМАНД ==========

@bot.message_handler(commands=['start'])
def start_command(message):
    """Старт"""
    bot.send_message(
        message.chat.id,
        "👋 **Добро пожаловать в мультичейн бот!**\n\n"
        "Я принимаю оплату в разных сетях:\n"
        "• TRON (TRX, USDT)\n"
        "• TON (Toncoin)\n"
        "• Ethereum (ETH, USDT)\n"
        "• Tether (USDT)\n"
        "• Bitcoin (BTC)\n\n"
        "Нажми **💰 Пополнить** чтобы начать",
        reply_markup=main_keyboard(),
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    """Помощь"""
    bot.send_message(
        message.chat.id,
        "📋 **Команды:**\n\n"
        "/start - приветствие\n"
        "/deposit - пополнить счет\n"
        "/networks - список сетей\n"
        "/help - это меню\n\n"
        "Кнопки в меню тоже работают 👇",
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['networks'])
def networks_command(message):
    """Показать доступные сети"""
    text = "📡 **Доступные сети для пополнения:**\n\n"
    for network in WALLETS.keys():
        text += f"{NETWORK_NAMES[network]}\n"
        text += f"Адрес: `{WALLETS[network]}`\n\n"

    bot.send_message(
        message.chat.id,
        text,
        parse_mode='Markdown'
    )

@bot.message_handler(commands=['deposit'])
def deposit_command(message):
    """Начало пополнения - выбор сети"""
    bot.send_message(
        message.chat.id,
        "🌐 **Выбери сеть для пополнения:**",
        reply_markup=network_selection_keyboard(),
        parse_mode='Markdown'
    )

# ========== ОБРАБОТЧИКИ ТЕКСТОВЫХ КНОПОК ==========

@bot.message_handler(func=lambda message: message.text == '💰 Пополнить')
def deposit_button(message):
    deposit_command(message)

@bot.message_handler(func=lambda message: message.text == '📋 Сети')
def networks_button(message):
    networks_command(message)

@bot.message_handler(func=lambda message: message.text == '❓ Помощь')
def help_button(message):
    help_command(message)

# ========== ОБРАБОТЧИКИ КОЛЛБЭКОВ ==========

@bot.callback_query_handler(func=lambda call: call.data.startswith('net_'))
def network_selected(call):
    """Выбрана сеть для пополнения"""
    user_id = call.message.chat.id
    network = call.data.replace('net_', '')

    # Создаем сессию пользователя
    user_sessions[user_id] = {
        'network': network,
        'status': 'waiting_login',
        'username': call.from_user.username or "NoUsername"
    }

    # Отвечаем на нажатие
    bot.answer_callback_query(call.id, f"Выбрана сеть {network}")

    # Запрашиваем логин
    bot.send_message(
        user_id,
        f"✅ Выбрана сеть: **{NETWORK_NAMES[network]}**\n\n"
        f"🔑 Теперь введи свой логин от сайта:",
        parse_mode='Markdown'
    )

    # Регистрируем следующий шаг
    bot.register_next_step_handler_by_chat_id(user_id, process_login)

@bot.callback_query_handler(func=lambda call: call.data == 'cancel')
def cancel_callback(call):
    """Отмена операции"""
    user_id = call.message.chat.id
    bot.answer_callback_query(call.id, "❌ Отменено")
    bot.send_message(
        user_id,
        "❌ Операция отменена. Для новой заявки используй /deposit"
    )

# ========== ОБРАБОТКА ЛОГИНА ==========

def process_login(message):
    """Обработка введенного логина"""
    user_id = message.chat.id
    login = message.text.strip()

    # Проверяем, есть ли сессия
    if user_id not in user_sessions:
        bot.send_message(
            user_id,
            "❌ Сессия не найдена. Начни заново с /deposit"
        )
        return

    # Валидация логина
    if len(login) < 3 or len(login) > 20:
        msg = bot.send_message(
            user_id,
            "❌ Логин должен быть от 3 до 20 символов. Попробуй еще раз:"
        )
        bot.register_next_step_handler(msg, process_login)
        return

    # Сохраняем логин в сессию
    user_sessions[user_id]['login'] = login
    user_sessions[user_id]['status'] = 'waiting_payment'

    # Получаем выбранную сеть
    network = user_sessions[user_id]['network']
    wallet_address = WALLETS[network]

    # Генерируем QR-код
    qr_image = generate_qr(wallet_address)

    # Текст с реквизитами
    text = (
        f"✅ **Логин сохранен:** `{login}`\n\n"
        f"🌐 **Сеть:** {NETWORK_NAMES[network]}\n"
        f"💰 **Адрес для оплаты:**\n"
        f"`{wallet_address}`\n\n"
        f"📸 **QR-код** с адресом ниже\n\n"
        f"⚠️ **Важно:**\n"
        f"• Отправляй ТОЛЬКО в выбранной сети\n"
        f"• После оплаты пришли скриншот в этот чат"
    )

    # Отправляем фото с QR и текстом
    bot.send_photo(
        user_id,
        qr_image,
        caption=text,
        parse_mode='Markdown'
    )

    # Логируем в консоль
    print(f"\n🆕 Новая заявка:")
    print(f"👤 Логин: {login}")
    print(f"🆔 TG ID: {user_id}")
    print(f"🌐 Сеть: {network}")
    print(f"💰 Адрес: {wallet_address}")
    print("-" * 40)

# ========== ОБРАБОТКА ФОТО ==========

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    """Сохраняем скриншоты оплаты"""
    user_id = message.chat.id
    user_data = user_sessions.get(user_id, {})

    login = user_data.get('login', 'unknown')
    network = user_data.get('network', 'unknown')

    # Получаем фото
    photo = message.photo[-1]
    file_id = photo.file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # Генерируем имя файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{SCREENSHOTS_DIR}/{timestamp}_{network}_{login}_{user_id}.jpg"

    # Сохраняем файл
    with open(filename, 'wb') as f:
        f.write(downloaded_file)

    # Подтверждаем пользователю
    bot.send_message(
        user_id,
        f"✅ Скриншот сохранен!\n"
        f"🌐 Сеть: {network}\n"
        f"👤 Логин: {login}\n\n"
        f"Администратор проверит оплату вручную."
    )

    # Логируем в консоль
    print(f"\n📸 Получен скриншот:")
    print(f"👤 Логин: {login}")
    print(f"🆔 TG ID: {user_id}")
    print(f"🌐 Сеть: {network}")
    print(f"💾 Файл: {filename}")
    print(f"🕐 Время: {timestamp}")
    print("=" * 50)

# ========== ОБРАБОТКА ВСЕГО ОСТАЛЬНОГО ==========

@bot.message_handler(func=lambda message: True)
def handle_all(message):
    """На любое другое сообщение"""
    bot.send_message(
        message.chat.id,
        "❓ Не понял команду.\n"
        "Используй /help или кнопки меню."
    )

# ========== ЗАПУСК ==========

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 МУЛЬТИЧЕЙН БОТ ЗАПУЩЕН")
    print("=" * 60)
    print("📡 Твои кошельки:")
    for net, addr in WALLETS.items():
        print(f"  {NETWORK_NAMES[net]}: {addr}")
    print("-" * 60)
    print(f"📁 Скриншоты сохраняются в: {SCREENSHOTS_DIR}/")
    print("🟢 Бот работает... Ctrl+C для остановки")
    print("=" * 60)

    bot.polling(none_stop=True)
