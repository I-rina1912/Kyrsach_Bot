# Курсовой проект: ТГ БОТ на pyTelebotApi
# Бот принимает у пользователя 2 фото, описание, категорию,
# сохраняет их в БазеДанных, собирает в один пост и публикует на канале


# Ипмортируем все необходимое
import sqlite3  # база данных
import hashlib
from datetime import datetime
import emoji  # эмоджи
import telebot  # сам телеграм бот
from config import token, photo_path  # токен от BotFather
from telebot import types
import requests


# CHANNEL_ID = '-1001814912527' #ID канала, в который бот будет публиковать голосование


class SqliteTelebot:
    def __init__(self):
        self.conn = sqlite3.connect('bd/database.db', check_same_thread=False)
        self.cursor = self.conn.cursor()

    def bd_new_vote(self, user_id, hash_vote):
        self.cursor.execute('''INSERT INTO vote (user_id, hash) VALUES (?, ?)''', (user_id, hash_vote.hexdigest()))

    def bd_upload_first_photo(self, b_photo, hash_vote):
        self.cursor.execute('''UPDATE vote SET photo_1=(?) WHERE hash=(?)''', (b_photo, hash_vote.hexdigest()))

    def bd_upload_second_photo(self, b_photo, hash_vote):
        self.cursor.execute('''UPDATE vote SET photo_2=(?) WHERE hash=(?)''', (b_photo, hash_vote.hexdigest()))

    def bd_dscrptn_add(self, dscrptn, hash_vote):
        self.cursor.execute('''UPDATE vote SET dscrptn=(?) WHERE hash=(?)''', (dscrptn, hash_vote.hexdigest()))

    def bd_category_add(self, category, hash_vote):
        self.cursor.execute('''UPDATE vote SET category=(?) WHERE hash=(?)''', (category, hash_vote.hexdigest()))

    def bd_check_add(self, hash_vote):
        self.cursor.execute('''SELECT photo_1, photo_2, dscrptn, category FROM vote WHERE hash=(?)''',
                            (hash_vote.hexdigest(),))
        return self.cursor.fetchone()

    def commit(self):
        self.conn.commit()


bot = telebot.TeleBot(token)
bd = SqliteTelebot()
hash_vote = hashlib.md5()


@bot.message_handler(commands=['start'])
def start(m, res=False):
    # Добавляем 2 основные кнопки
    markup = types.ReplyKeyboardMarkup(resize_keyboard=False)
    item1 = types.KeyboardButton('💬 Создать новый Vote')
    item2 = types.KeyboardButton('👁‍🗨 Статистика')
    item3 = types.KeyboardButton('📩 Связаться с разработчиками')
    markup.add(item1)
    markup.add(item2)
    markup.add(item3)
    bot.send_message(m.chat.id, f'{m.from_user.first_name}, давай начнём 🔥\n'
                                'Выбери одну из кнопок ⬇️:'
                     , reply_markup=markup)


@bot.message_handler(content_types=['text'])
def button(message):
    global hash_vote

    if message.text == '💬 Создать новый Vote':
        hash_vote = hashlib.md5(
            str(message.from_user.id).encode() + datetime.strftime(datetime.now(), '%d%m%Y%H%M%S').encode())
        bd.bd_new_vote(message.from_user.id, hash_vote)
        photo_1 = bot.send_message(message.chat.id, 'Отправь мне первое фото для твоего Vote 📸: ')
        bot.register_next_step_handler(photo_1, get_1photo_message)

    # Здесь будет код для статистики
    elif message.text == '👁‍🗨 Статистика':
        statistic = bot.send_message(message.chat.id, 'Статистика пока что недоступна 🥲\n'
                                                      'Но я скоро обязательно этому научусь!\n\n'
                                                      'А пока что давай создадим новый Vote.\n'
                                                      'Нажми кнопку "Создать новый Vote" ⬇️')
        bot.register_next_step_handler(statistic, button)

    elif (message.text == '📩 Связаться с разработчиками'):
        help = bot.send_message(message.chat.id, 'Что-то не работает? 🙉\n'
                                                 'Сделай скриншот и отправь сюда:\n'
                                                 '@dima_brand или @massage_irenka\n\n'
                                                 'Но давай всё равно попробуем создать новый Vote!\n'
                                                 'Нажми кнопку "Создать новый Vote" ⬇️:')
        bot.register_next_step_handler(help, button)


@bot.message_handler(content_types=['photo'])
def get_1photo_message(message):
    global hash_vote
    photo_2 = bot.send_message(message.chat.id, 'Отлично!\nА теперь отправь второе фото для сравнения 📸: ')
    fileID = message.photo[-1].file_id
    file_info = bot.get_file(fileID)
    downloaded_file = bot.download_file(file_info.file_path)
    bd.bd_upload_first_photo(downloaded_file, hash_vote)
    bot.register_next_step_handler(photo_2, get_2photo_message)


@bot.message_handler(content_types=['photo'])
def get_2photo_message(message):
    global hash_vote
    dscrptn = bot.send_message(message.chat.id,
                               'Cупер!\nА теперь загрузи описание для своего Vote 📝\n(не более 200 знаков): ')
    fileID = message.photo[-1].file_id
    file_info = bot.get_file(fileID)
    downloaded_file = bot.download_file(file_info.file_path)
    bd.bd_upload_second_photo(downloaded_file, hash_vote)
    bot.register_next_step_handler(dscrptn, get_dscrptn_message)


@bot.message_handler(content_types=['text'])
def get_dscrptn_message(message):
    global hash_vote
    ln = len(message.text)
    if ln > 200:
        bot.send_message(message.chat.id, '❌ Слишком много текста, устанут читать, давай ещё раз: ')
    else:
        bd.bd_dscrptn_add(message.text, hash_vote)

        markup = types.ReplyKeyboardMarkup(resize_keyboard=False)
        ktg1 = types.KeyboardButton('#Авто 🚘')
        ktg2 = types.KeyboardButton('#Собачки 🐶')
        ktg3 = types.KeyboardButton('#Котики 🐱')
        ktg4 = types.KeyboardButton('#Люди 👤')
        ktg5 = types.KeyboardButton('#Гаджеты 📱')
        ktg6 = types.KeyboardButton('#Недвижимость 🏢')
        ktg7 = types.KeyboardButton('#Путешествия 🏝')
        ktg8 = types.KeyboardButton('#Другое 🔄')
        markup.add(ktg1)
        markup.add(ktg2)
        markup.add(ktg3)
        markup.add(ktg4)
        markup.add(ktg5)
        markup.add(ktg6)
        markup.add(ktg7)
        markup.add(ktg8)

        bot.send_message(message.chat.id, 'Почти готово!\n'
                                          'Осталось выбрать подходящую категорию:')
        ktg = bot.send_message(message.chat.id, '🗂'
                               , reply_markup=markup)

        bot.register_next_step_handler(ktg, category)


@bot.message_handler(content_types=['text'])
def category(message):
    global hash_vote

    if message.text == '#Авто 🚘':
        bd.bd_category_add(message.text, hash_vote)
    elif message.text == '#Собачки 🐶':
        bd.bd_category_add(message.text, hash_vote)
    elif message.text == '#Котики 🐱':
        bd.bd_category_add(message.text, hash_vote)
    elif message.text == '#Люди 👤':
        bd.bd_category_add(message.text, hash_vote)
    elif message.text == '#Гаджеты 📱':
        bd.bd_category_add(message.text, hash_vote)
    elif message.text == '#Недвижимость 🏢':
        bd.bd_category_add(message.text, hash_vote)
    elif message.text == '#Путешествия 🏝':
        bd.bd_category_add(message.text, hash_vote)
    elif message.text == '#Другое 🔄':
        bd.bd_category_add(message.text, hash_vote)
    bd.commit()

    markup = types.ReplyKeyboardMarkup(resize_keyboard=False)
    ch = types.KeyboardButton('🔍 Проверить')
    pub = types.KeyboardButton('✅ Опубликовать')
    res = types.KeyboardButton('🔁 Restart')
    markup.add(ch)
    markup.add(pub)
    markup.add(res)
    result = bot.send_message(message.chat.id, 'Всё готово 🔥\n'
                                               'Нажми кнопку ⬇️',
                              reply_markup=markup)
    bot.register_next_step_handler(result, vote)


@bot.message_handler(content_types=['text'])
def vote(message):
    global hash_vote

    if message.text == '🔍 Проверить':
        result = bd.bd_check_add(hash_vote)
        a = bot.send_photo(message.chat.id, result[0])
        b = bot.send_photo(message.chat.id, result[1])
        c = bot.send_message(message.chat.id, result[2])
        d = bot.send_message(message.chat.id, result[3])
        check = bot.send_message(message.chat.id, '\n\n'
                                                  'Все в порядке? Тогда жми "Опубликовать"!\n'
                                                  'Что-то не так? Тогда жми "Restart"')
        bot.register_next_step_handler(check, vote)

    elif message.text == '✅ Опубликовать':
        CHANNEL_ID = '-1001814912527'
        result = bd.bd_check_add(hash_vote)
        r1 = bot.send_message(CHANNEL_ID, result[3])
        r2 = bot.send_message(CHANNEL_ID, result[2])
        r3 = bot.send_photo(CHANNEL_ID, result[0])
        r4 = bot.send_photo(CHANNEL_ID, result[1])

        push = bot.send_photo(CHANNEL_ID, 'Поздравляю! Ваш Vote готов!')
        public = bot.send_message(message.chat.id, 'Теперь ты можешь найти свой Vote здесь:\n'
                                                   '@VoteForPic')
        # bot.register_next_step_handler(push, start)

    elif message.text == '🔁 Restart':
        rstrt = bot.send_message(message.chat.id, 'Понял, давай всё по новой 😌!\n'
                                                  'Жми любую кнопку:')
        bot.register_next_step_handler(rstrt, start)


bot.polling(none_stop=True, interval=0)
