import telebot
from telebot import types
from database_sqlite import DatabaseManager
from models_sqlite import User, Event, Exhibition, MuseumInfo
from datetime import datetime
import logging
import os
from functools import wraps
import urllib.request
import io

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('museum_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

TOKEN = '8156140134:AAGouWNzQs-QKBRNmB8De3-rK0H_OcmrpqI'
TICKET_URL = 'https://artmus.ru/information/cost/'
db_manager = DatabaseManager('museum_bot.db')
bot = telebot.TeleBot(TOKEN)



def download_image(url):
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req) as response:
            return response.read()
    except Exception as e:
        logger.error(f"Ошибка загрузки изображения: {e}")
        return None


def send_photo_with_caption(chat_id, image_url, caption, reply_markup=None):
    try:
        if image_url and image_url.startswith('http'):
            image_data = download_image(image_url)
            if image_data:
                bot.send_photo(
                    chat_id,
                    image_data,
                    caption=caption,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
                return True
    except Exception as e:
        logger.error(f"Ошибка отправки изображения: {e}")

    bot.send_message(chat_id, caption, reply_markup=reply_markup, parse_mode='HTML')
    return False


# Инициализация базы данных
def init_database():
    try:
        if not os.path.exists('museum_bot.db'):
            db_manager.init_db()
            db_manager.populate_initial_data()
            logger.info("База данных создана и заполнена")
        else:
            logger.info("База данных уже существует")
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")


init_database()


# Декоратор для регистрации пользователя
def register_user(func):
    @wraps(func)
    def wrapper(message):
        try:
            with db_manager.session_scope() as session:
                # Пытаемся найти пользователя
                user = session.query(User).filter_by(
                    telegram_id=message.from_user.id
                ).first()

                if not user:
                    # Создаем нового пользователя
                    user = User(
                        telegram_id=message.from_user.id,
                        username=message.from_user.username,
                        first_name=message.from_user.first_name,
                        last_name=message.from_user.last_name
                    )
                    session.add(user)
                    session.flush()  # Принудительно применяем изменения
                    logger.info(f"Новый пользователь зарегистрирован: {message.from_user.id}")
                else:
                    # Обновляем информацию о существующем пользователе
                    user.username = message.from_user.username
                    user.first_name = message.from_user.first_name
                    user.last_name = message.from_user.last_name
                    user.last_activity = datetime.utcnow()
                    logger.info(f"Существующий пользователь обновлен: {message.from_user.id}")

                session.commit()

        except Exception as e:
            logger.error(f"Ошибка регистрации пользователя: {e}")
            pass

        return func(message)

    return wrapper


def create_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        '🏛️ О музее',
        '🖼️ Экспозиции',
        '📅 Мероприятия',
        '📍 Как добраться',
        '🎫 Купить билет',
        '📞 Контакты',
        '❓ Помощь'
    ]
    markup.add(*[types.KeyboardButton(btn) for btn in buttons])
    return markup


@bot.message_handler(commands=['start'])
@register_user
def send_welcome(message):
    user_name = message.from_user.first_name

    with db_manager.session_scope() as session:
        museum = session.query(MuseumInfo).first()
        if museum and museum.main_image:
            caption = (
                f"Добро пожаловать в музейный гид, {user_name}! 🎨\n\n"
                f"Я помогу вам узнать о выставках и мероприятиях музея.\n"
                f"Также вы можете узнать как добраться и купить билеты онлайн.\n"
                f"Выберите интересующий раздел в меню ниже:"
            )
            send_photo_with_caption(
                message.chat.id,
                museum.main_image,
                caption,
                create_main_menu()
            )
        else:
            welcome_text = (
                f"Добро пожаловать в музейный гид, {user_name}! 🎨\n\n"
                f"Я помогу вам узнать о выставках и мероприятиях музея.\n"
                f"Также вы можете узнать как добраться и купить билеты онлайн.\n"
                f"Выберите интересующий раздел в меню ниже:"
            )
            bot.send_message(
                message.chat.id,
                welcome_text,
                reply_markup=create_main_menu()
            )


@bot.message_handler(func=lambda message: True)
@register_user
def handle_message(message):
    text = message.text

    handlers = {
        '🏛️ О музее': send_museum_info,
        '🖼️ Экспозиции': send_exhibitions,
        '📅 Мероприятия': send_events,
        '📍 Как добраться': send_directions,
        '🎫 Купить билет': send_ticket_link,
        '📞 Контакты': send_contacts,
        '❓ Помощь': send_help
    }

    handler = handlers.get(text)
    if handler:
        handler(message)
    else:
        bot.send_message(
            message.chat.id,
            "Извините, я не понимаю эту команду. Используйте меню для навигации."
        )


def send_museum_info(message):
    try:
        with db_manager.session_scope() as session:
            museum = session.query(MuseumInfo).first()

            if museum:
                text = (
                    f"🏛️ <b>{museum.name}</b>\n\n"
                    f"📍 Адрес: {museum.address}\n"
                    f"🕒 Часы работы: {museum.work_hours}\n"
                    f"📞 Телефон: {museum.phone}\n"
                    f"🌐 Сайт: {museum.website}\n"
                    f"💰 {museum.price_info}\n\n"
                    f"{museum.description}"
                )

                if museum.gallery_images:
                    send_photo_with_caption(
                        message.chat.id,
                        museum.gallery_images,
                        text
                    )
                else:
                    bot.send_message(message.chat.id, text, parse_mode='HTML')
            else:
                bot.send_message(message.chat.id, "Информация о музее временно недоступна")
    except Exception as e:
        logger.error(f"Ошибка получения информации о музее: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении информации")


def send_exhibitions(message):
    try:
        with db_manager.session_scope() as session:
            permanent = session.query(Exhibition).filter_by(
                type='permanent',
                is_active=True
            ).first()

            temporary = session.query(Exhibition).filter(
                Exhibition.type == 'temporary',
                Exhibition.is_active == True
            ).all()

            if permanent:
                text = f"🖼️ <b>Постоянная экспозиция:</b>\n\n"
                text += f"<b>{permanent.name}</b>\n"
                text += f"{permanent.description}\n"

                if permanent.poster_image:
                    send_photo_with_caption(
                        message.chat.id,
                        permanent.poster_image,
                        text
                    )
                else:
                    bot.send_message(message.chat.id, text, parse_mode='HTML')

            if temporary:
                bot.send_message(
                    message.chat.id,
                    "🖼️ <b>Временные выставки:</b>",
                    parse_mode='HTML'
                )

                for exp in temporary:
                    exp_text = (
                        f"<b>{exp.name}</b>\n"
                        f"📅 {exp.start_date.strftime('%d.%m')} - {exp.end_date.strftime('%d.%m.%Y')}\n"
                        f"👤 Куратор: {exp.curator}\n"
                        f"{exp.description}\n"
                    )

                    if exp.poster_image:
                        send_photo_with_caption(
                            message.chat.id,
                            exp.poster_image,
                            exp_text
                        )
                    else:
                        bot.send_message(message.chat.id, exp_text, parse_mode='HTML')
            elif not permanent:
                bot.send_message(message.chat.id, "В настоящее время выставки не проводятся")

    except Exception as e:
        logger.error(f"Ошибка получения выставок: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении списка выставок")


def send_events(message):
    try:
        with db_manager.session_scope() as session:
            events = session.query(Event).filter(
                Event.start_datetime >= datetime.now(),
                Event.is_active == True
            ).order_by(Event.start_datetime).limit(10).all()

            if events:
                bot.send_message(
                    message.chat.id,
                    "📅 <b>Ближайшие мероприятия:</b>",
                    parse_mode='HTML'
                )

                for event in events:
                    event_date = event.start_datetime.strftime('%d.%m.%Y')
                    event_time = event.start_datetime.strftime('%H:%M')

                    type_icons = {
                        'excursion': '🚶',
                        'lecture': '📚',
                        'masterclass': '🎨',
                        'concert': '🎵',
                        'other': '📌'
                    }
                    icon = type_icons.get(event.event_type, '📌')

                    event_text = (
                        f"{icon} <b>{event.name}</b>\n"
                        f"📅 {event_date} в {event_time}\n"
                        f"📍 {event.location or 'Уточняйте'}\n"
                        f"💰 {event.price}\n"
                        f"📝 {event.description}\n"
                    )

                    if event.poster_image:
                        send_photo_with_caption(
                            message.chat.id,
                            event.poster_image,
                            event_text
                        )
                    else:
                        bot.send_message(
                            message.chat.id,
                            event_text,
                            parse_mode='HTML'
                        )
            else:
                text = "На ближайшее время мероприятия не запланированы.\n\n"
                text += "Следите за обновлениями в нашем канале: @museum_channel"
                bot.send_message(message.chat.id, text)

    except Exception as e:
        logger.error(f"Ошибка получения мероприятий: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении списка мероприятий")


def send_directions(message):
    """Отправка информации о том, как добраться, с картой"""
    try:
        with db_manager.session_scope() as session:
            museum = session.query(MuseumInfo).first()

            markup = types.InlineKeyboardMarkup(row_width=2)

            # Кнопка Яндекс.Карты
            yandex_btn = types.InlineKeyboardButton(
                "Яндекс.Карты",
                url=f"https://yandex.ru/maps/?text={museum.address.replace(' ', '+')}"
            )

            # Кнопка Google Карты
            google_btn = types.InlineKeyboardButton(
                "Google Maps",
                url=f"https://www.google.com/maps/search/?api=1&query={museum.address.replace(' ', '+')}"
            )

            # Кнопка 2ГИС
            dgis_btn = types.InlineKeyboardButton(
                "2ГИС",
                url=f"https://2gis.ru/search/{museum.address.replace(' ', '%20')}"
            )

            markup.add(yandex_btn, google_btn, dgis_btn)

            if museum:
                text = (
                    f"📍 <b>Как добраться до музея</b>\n\n"
                    f"<b>Адрес:</b> {museum.address}\n\n"
                    f"<b>На метро:</b>\n"
                    f"🚇 станция 'Алабинская' (4,3 км)\n\n"
                    f"<b>Наземный транспорт:</b>\n"
                    f"🚌 Автобусы: №15, №20 до остановки 'Ул. Некрасовская'; №3, №8 до остановки 'Ул. Куйбышева'\n"
                    f"🚎 Троллейбусы: №1, №12 до остановки 'Ул. Некрасовская'\n\n"
                    f"<b>На автомобиле:</b>\n"
                    f"🚗 Платная парковка на ул. Тверская (200 руб/час)\n"
                    f"🅿️ Бесплатная парковка в выходные\n\n"
                    f"👇 <b>Открыть на карте:</b>"
                )

                if museum.latitude and museum.longitude:
                    text += f"\n\nКоординаты для навигатора: {museum.latitude}, {museum.longitude}"

                bot.send_message(
                    message.chat.id,
                    text,
                    parse_mode='HTML',
                    reply_markup=markup
                )
            else:
                text = (
                    f"📍 <b>Как добраться до музея</b>\n\n"
                    f"<b>Адрес:</b> г. Москва, ул. Тверская, 15\n\n"
                    f"<b>На метро:</b>\n"
                    f"🚇 станция 'Тверская' (выход к ул. Тверская)\n\n"
                    f"<b>Наземный транспорт:</b>\n"
                    f"🚌 Автобусы: №15, №20 до остановки 'Музей искусств'\n\n"
                    f"👇 <b>Открыть на карте:</b>"
                )

                bot.send_message(
                    message.chat.id,
                    text,
                    parse_mode='HTML',
                    reply_markup=markup
                )
    except Exception as e:
        logger.error(f"Ошибка получения информации о проезде: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении информации о проезде")


def send_ticket_link(message):
    try:
        with db_manager.session_scope() as session:
            museum = session.query(MuseumInfo).first()

            markup = types.InlineKeyboardMarkup()
            ticket_btn = types.InlineKeyboardButton(
                "🎫 Купить билет онлайн",
                url=TICKET_URL
            )
            markup.add(ticket_btn)

            if museum:
                price_info = museum.price_info
            else:
                price_info = "Взрослый: 500 руб., Льготный: 250 руб."

            text = (
                f"🎫 <b>Покупка билетов в музей</b>\n\n"
                f"<b>Стоимость билетов:</b>\n"
                f"{price_info}\n\n"
                f"<b>Способы покупки:</b>\n"
                f"• Онлайн на нашем сайте (кнопка ниже)\n"
                f"• В кассе музея (наличные/карта)\n"
                f"• В терминалах самообслуживания в холле\n\n"
                f"<b>Льготные категории:</b>\n"
                f"• Студенты - скидка 50%\n"
                f"• Пенсионеры - скидка 30%\n"
                f"• Дети до 7 лет - бесплатно\n\n"
                f"👇 <b>Нажмите кнопку ниже для покупки онлайн</b>"
            )

            bot.send_message(
                message.chat.id,
                text,
                parse_mode='HTML',
                reply_markup=markup
            )
    except Exception as e:
        logger.error(f"Ошибка отправки ссылки на билеты: {e}")
        bot.send_message(message.chat.id, "Произошла ошибка при получении информации о билетах")


def send_contacts(message):
    try:
        with db_manager.session_scope() as session:
            museum = session.query(MuseumInfo).first()

            if museum:
                text = (
                    f"📞 <b>Контакты музея:</b>\n\n"
                    f"📱 Телефон: {museum.phone}\n"
                    f"📧 Email: info@{museum.website}\n"
                    f"🌐 Сайт: www.{museum.website}\n\n"
                    f"📍 Адрес: {museum.address}\n"
                    f"🕒 Часы работы: {museum.work_hours}\n\n"
                    f"📱 Мы в соцсетях:\n"
                    f"   • VK: vk.com/djka4an\n"
                    f"   • Telegram: @ka4annn"
                )
    except Exception as e:
        logger.error(f"Ошибка получения контактов: {e}")
        text = "Произошла ошибка при получении контактной информации"

    bot.send_message(message.chat.id, text, parse_mode='HTML')


def send_help(message):
    help_text = (
        "❓ <b>Справка по использованию бота:</b>\n\n"
        "<b>Доступные разделы:</b>\n"
        "🏛️ О музее - общая информация о музее\n"
        "🖼️ Экспозиции - текущие выставки\n"
        "📅 Мероприятия - расписание событий\n"
        "📍 Как добраться - схема проезда и карты\n"
        "🎫 Купить билет - покупка билетов онлайн\n"
        "📞 Контакты - телефоны, адрес, соцсети\n\n"
        "<b>Команды:</b>\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать эту справку"
    )
    bot.send_message(message.chat.id, help_text, parse_mode='HTML')


if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("Музейный бот запущен и готов к работе!")
    logger.info("Доступные разделы: О музее, Экспозиции, Мероприятия, Как добраться, Купить билет, Контакты, Помощь")
    logger.info("=" * 50)

    try:
        bot.remove_webhook()
        bot.infinity_polling(timeout=60, long_polling_timeout=60)
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")