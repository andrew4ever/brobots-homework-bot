from os import listdir
from os.path import isfile, join


def classes_list(config):
    path = config['DB']['PATH']

    files = [f for f in listdir(path) if isfile(join(path, f))]
    files = [f.split('.')[0] for f in files if f.split('.')[-1] == 'json']
    files.remove('subjects')

    return files
