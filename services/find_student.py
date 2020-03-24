from services import classes_list
import tinydb


def find_student(u_id, config):
    classes = classes_list(config)

    for c in classes:
        db = tinydb.TinyDB(config['DB']['CLASSES']['PATH'].format(c))

        for s in db:
            if s['telegramId'] == str(u_id):
                s['classId'] = c
                return s

    return None
