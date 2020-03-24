import os

import telebot
import tinydb
from telebot import types

import services
from config import config

if not os.path.exists(config['DB']['PATH']):
    os.makedirs(os.path.dirname(config['DB']['PATH']), exist_ok=True)

bot = telebot.TeleBot(config['BOT']['TOKEN'])
subjectsDb = tinydb.TinyDB(config['DB']['SUBJECTS']['PATH'])
queue = []


@bot.message_handler(commands=['start'])
def start_menu(message: types.Message):
    bot.reply_to(message, config['BOT']['START'])


@bot.message_handler(commands=['teacher_request'])
def add_teacher(message: types.Message):
    kb = types.ReplyKeyboardMarkup(row_width=1)

    for sub in subjectsDb:
        kb.add(
            types.KeyboardButton(
                ' '.join([sub['name'], sub['classId']])
            )
        )

    bot.reply_to(message, config['BOT']['CHOOSE_SUBJECT'], reply_markup=kb)


@bot.message_handler(commands=['create_class'])
def create_class(message: types.Message):
    u = message.from_user

    if not services.is_admin(u.id, config):
        bot.reply_to(message, config['BOT']['NO_ACCESS'])
        return

    bot.reply_to(message, config['BOT']['ENTER_CLASS_NAME'])
    queue.append((u.id, 'new_class_name'))


@bot.message_handler(commands=['create_subject'])
def create_subject(message: types.Message):
    u = message.from_user

    if not services.is_admin(u.id, config):
        bot.reply_to(message, config['BOT']['NO_ACCESS'])
        return

    bot.reply_to(message, config['BOT']['ENTER_SUBJECT_NAME'])
    queue.append((u.id, 'subject_name'))


@bot.message_handler(content_types=['text'])
def text_answers(message: types.Message):
    for i in queue:
        if i[0] != message.chat.id:
            continue

        if i[1] == 'new_class_name':
            tinydb.TinyDB(
                config['DB']['CLASSES']['PATH'].format(message.text))
            bot.reply_to(message, config['BOT']['SUCCESS'])

        elif i[1] == 'subject_name':
            classes = services.classes_list(config)

            if not classes:
                bot.reply_to(message, config['BOT']['NO_CLASSES'])
                queue.remove(i)
                return

            kb = types.InlineKeyboardMarkup(row_width=1)
            for c in classes:
                kb.row(
                    types.InlineKeyboardButton(
                        c, callback_data='create_subject:{}:{}'.format(
                            message.text, c)
                    )
                )

            bot.reply_to(message, config['BOT']
                         ['CHOOSE_CLASS'], reply_markup=kb)

        queue.remove(i)


@bot.callback_query_handler(func=lambda call: True)
def inline_button(callback: types.CallbackQuery):
    u = callback.from_user

    title = callback.data.split(':')[0]
    val = callback.data.split(':')[1:]

    if title == 'create_subject':
        subjectsDb.insert(
            {'name': val[0], 'classId': val[1], 'teacherId': None})
        bot.send_message(u.id, config['BOT']['SUCCESS'])


if __name__ == '__main__':
    bot.polling(none_stop=True)
