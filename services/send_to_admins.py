def send_to_admins(bot, config, message_text, args=(), kwargs={}):
    for admin in config['ADMINS']:
        try:
            bot.send_message(admin, message_text, *args, **kwargs)

        except:
            print('Unable to send message to admin; id: %s' % admin)
