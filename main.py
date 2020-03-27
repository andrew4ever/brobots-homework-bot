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
Subject = tinydb.Query()

queue = []
homework = []


@bot.message_handler(commands=['start'])
def start_menu(message: types.Message):
    bot.reply_to(message, config['BOT']['START'])


@bot.message_handler(commands=['send_homework'])
def homework_start(message: types.Message):
    bot.reply_to(message, config['BOT']['HOMEWORK_INSTRUCTIONS'])
    homework.append([message.chat.id, []])


@bot.message_handler(commands=['done'])
def homework_done(message: types.Message):
    if not [i for i in homework if i[0] == message.chat.id]:
        return

    student = services.find_student(message.chat.id, config)
    classId = student['classId']

    kb = types.InlineKeyboardMarkup()

    for s in subjectsDb.search(Subject.classId == classId):
        kb.add(
            types.InlineKeyboardButton(
                text='{} - {}'.format(s['name'], s['classId']),
                callback_data='send_hw:{}:{}'.format(
                    s['name'], s['classId'])
            )
        )

    if not len(subjectsDb):
        bot.reply_to(message, config['BOT']['NO_SUBJECTS'])
        return

    bot.reply_to(message,
                 config['BOT']['CHOOSE_SUBJECT'], reply_markup=kb)


@bot.message_handler(commands=['cancel'])
def cancel_request(message: types.Message):
    for i in queue:
        if i[0] == message.chat.id:
            queue.remove(i)

    for i in homework:
        if i[0] == message.chat.id:
            homework.remove(i)

    bot.reply_to(message, config['BOT']['SUCCESS'])


@bot.message_handler(commands=['commands'])
def admin_commands(message: types.Message):
    if not services.is_admin(message.chat.id, config):
        bot.reply_to(message, config['BOT']['NO_ACCESS'])
        return

    bot.reply_to(message, config['BOT']['ADMIN_COMMANDS'])


@bot.message_handler(commands=['subjects'])
def all_subjects(message: types.Message):
    if not services.is_admin(message.chat.id, config):
        bot.reply_to(message, config['BOT']['NO_ACCESS'])
        return

    base = config['BOT']['SUBJECTS_LIST']

    for s in subjectsDb:
        base += '{} - {} - {}\n'.format(
            s['name'],
            s['classId'],
            s['teacherId']
        )

    if not len(subjectsDb):
        bot.reply_to(message, config['BOT']['NO_SUBJECTS'])
        return

    bot.reply_to(message, base)


@bot.message_handler(commands=['classes'])
def all_classes(message: types.Message):
    if not services.is_admin(message.chat.id, config):
        bot.reply_to(message, config['BOT']['NO_ACCESS'])
        return

    kb = types.InlineKeyboardMarkup()
    classes = services.classes_list(config)

    for c in classes:
        kb.add(
            types.InlineKeyboardButton(
                text=c,
                callback_data='show_st:{}'.format(c)
            )
        )

    if not len(classes):
        bot.reply_to(message, config['BOT']['NO_CLASSES'])
        return

    bot.reply_to(message, config['BOT']['CHOOSE_CLASS'], reply_markup=kb)


@bot.message_handler(commands=['create_subject'])
def create_subject(message: types.Message):
    u = message.from_user

    if not services.is_admin(u.id, config):
        bot.reply_to(message, config['BOT']['NO_ACCESS'])
        return

    bot.reply_to(message, config['BOT']['ENTER_SUBJECT_NAME'])
    queue.append((u.id, 'subject_name'))


@bot.message_handler(commands=['create_class'])
def create_class(message: types.Message):
    u = message.from_user

    if not services.is_admin(u.id, config):
        bot.reply_to(message, config['BOT']['NO_ACCESS'])
        return

    bot.reply_to(message, config['BOT']['ENTER_CLASS_NAME'])
    queue.append((u.id, 'new_class_name'))


@bot.message_handler(commands=['student_request'])
def add_student(message: types.Message):
    bot.reply_to(message, config['BOT']['ENTER_NAME'])
    queue.append((message.chat.id, 'student_request'))


@bot.message_handler(commands=['teacher_request'])
def add_teacher(message: types.Message):
    u = message.from_user

    if not len(subjectsDb):
        bot.reply_to(message, config['BOT']['NO_SUBJECTS'])
        return

    kb = types.ReplyKeyboardMarkup(one_time_keyboard=True)

    for sub in subjectsDb:
        kb.add(
            types.KeyboardButton(
                '{} - {}'.format(sub['name'], sub['classId'])
            )
        )

    bot.reply_to(message, config['BOT']['CHOOSE_SUBJECT'], reply_markup=kb)
    queue.append((u.id, 'teacher_request'))


@bot.message_handler(content_types=['text', 'audio', 'document', 'photo'])
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
                        c, callback_data='add_su:{}:{}'.format(
                            message.text, c)
                    )
                )

            bot.reply_to(message, config['BOT']
                         ['CHOOSE_CLASS'], reply_markup=kb)

        elif i[1] == 'teacher_request':
            bot.reply_to(
                message, config['BOT']['REQUEST_SENT'],
                reply_markup=types.ReplyKeyboardRemove()
            )

            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(
                text=config['BOT']['KEYBOARDS']['YES'],
                callback_data='at:{}:{}'.format(
                    message.chat.id, message.text
                ))
            )

            services.send_to_admins(
                bot, config,
                config['BOT']['ADD_TEACHER'].format(
                    message.text, services.username(message.from_user)),
                kwargs={'reply_markup': kb})

        elif i[1] == 'student_request':
            classes = services.classes_list(config)

            if not len(classes):
                bot.reply_to(message, config['BOT']['NO_CLASSES'])

            kb = types.ReplyKeyboardMarkup(one_time_keyboard=True)

            for c in classes:
                kb.add(
                    types.KeyboardButton('{}:{}'.format(c, message.text))
                )

            bot.reply_to(message, config['BOT']
                         ['CHOOSE_CLASS'], reply_markup=kb)
            queue.append((message.chat.id, 'student_register'))

        elif i[1] == 'student_register':
            bot.reply_to(
                message, config['BOT']['REQUEST_SENT'],
                reply_markup=types.ReplyKeyboardRemove()
            )

            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(
                text=config['BOT']['KEYBOARDS']['YES'],
                callback_data='add_st:{}:{}'.format(
                    message.chat.id, message.text
                ))
            )

            services.send_to_admins(
                bot, config,
                config['BOT']['ADD_STUDENT'].format(
                    *message.text.split(':')),
                kwargs={'reply_markup': kb})

        queue.remove(i)

    for i in homework:
        if i[0] != message.chat.id:
            continue

        i[1].append(message.message_id)


@bot.callback_query_handler(func=lambda call: True)
def inline_button(callback: types.CallbackQuery):
    u = callback.from_user

    title = callback.data.split(':')[0]
    val = callback.data.split(':')[1:]

    if title == 'add_su':
        subjectsDb.insert(
            {'name': val[0], 'classId': val[1], 'teacherId': None})
        bot.send_message(u.id, config['BOT']['SUCCESS'])

    elif title == 'at':
        subject, classId = val[1].split(' - ')

        subjectsDb.update(
            {'teacherId': val[0]},
            (Subject.name == subject) & (Subject.classId == classId)
        )

        bot.send_message(u.id, config['BOT']['SUCCESS'])
        bot.send_message(val[0], config['BOT']['APPROVED'])

        bot.edit_message_text(callback.message.text + '\n\n' +
                              config['BOT']['APPROVED'], u.id,
                              callback.message.message_id)

    elif title == 'add_st':
        studentDb = tinydb.TinyDB(
            config['DB']['CLASSES']['PATH'].format(val[1]))

        for s in studentDb:
            if s['telegramId'] == val[0]:
                bot.edit_message_text(callback.message.text + '\n\n' +
                                      config['BOT']['APPROVED'], u.id,
                                      callback.message.message_id)
                return

        studentDb.insert({'telegramId': val[0], 'name': val[2]})

        bot.send_message(u.id, config['BOT']['SUCCESS'])
        bot.send_message(val[0], config['BOT']['APPROVED'])
        bot.send_message(val[0], config['BOT']['HOMEWORK_PREINSTRUCTIONS'])

        bot.edit_message_text(callback.message.text + '\n\n' +
                              config['BOT']['APPROVED'], u.id,
                              callback.message.message_id)

    elif title == 'show_st':
        studentDb = tinydb.TinyDB(
            config['DB']['CLASSES']['PATH'].format(val[0]))

        base = config['BOT']['STUDENTS_LIST']

        for s in studentDb:
            base += s['name']
            base += '\n'

        if not len(studentDb):
            base += config['BOT']['EMPTY_LIST']

        bot.edit_message_text(base, callback.from_user.id,
                              callback.message.message_id)

    elif title == 'send_hw':
        s = subjectsDb.search(
            (Subject.name == val[0]) & (Subject.classId == val[1]))[0]
        student = services.find_student(callback.from_user.id, config)

        for i in homework:
            if i[0] != u.id:
                continue

            try:
                bot.send_message(s['teacherId'], config['BOT']
                                 ['NEW_HOMEWORK'].format(student['name']))

                for m in i[1]:
                    bot.forward_message(s['teacherId'], i[0], m)

                bot.send_message(s['teacherId'], config['BOT']
                                 ['NEW_HOMEWORK_END'])
            except:
                bot.send_message(u.id, config['BOT']['FAILURE'])

        bot.send_message(u.id, config['BOT']['SUCCESS'])


if __name__ == '__main__':
    bot.polling(none_stop=True)
