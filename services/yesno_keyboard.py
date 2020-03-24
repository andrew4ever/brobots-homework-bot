from telebot import types


def yesno_keyboard(config, cb_title):
    keyboard = types.InlineKeyboardMarkup()

    y = types.InlineKeyboardButton(
        text=config['BOT']['KEYBOARDS']['YES'], callback_data=f'{cb_title}:1')

    n = types.InlineKeyboardButton(
        text=config['BOT']['KEYBOARDS']['NO'], callback_data=f'{cb_title}:0')

    keyboard.row(y, n)

    return keyboard
