from collections import OrderedDict
from fbs import path
from fbs_runtime import FbsError
from getpass import getpass
from os.path import exists

BASE_JSON = 'src/build/settings/base.json'
SECRET_JSON = 'src/build/settings/secret.json'

def prompt_for_value(
    value, optional=False, default='', password=False, choices=()
):
    message = value
    if choices:
        choices_dict = \
            OrderedDict((str(i + 1), c) for (i, c) in enumerate(choices))
        message += ': '
        message += ' or '.join('%s) %s' % tpl for tpl in choices_dict.items())
    if default:
        message += ' [%s] ' % \
                   (choices.index(default) + 1 if choices else default)
    message += ': '
    prompt = getpass if password else input
    result = prompt(message).strip()
    if not result and default:
        print(default)
        return default
    if not optional:
        while not result or (choices and result not in choices_dict):
            result = prompt(message).strip()
    return choices_dict[result] if choices else result

def require_existing_project():
    if not exists(path('src')):
        raise FbsError(
            "Could not find the src/ directory. Are you in the right folder?\n"
            "If yes, did you already run\n"
            "    fbs startproject ?"
        )

def require_frozen_app():
    if not exists(path('${freeze_dir}')):
        raise FbsError(
            'It seems your app has not yet been frozen. Please run:\n'
            '    fbs freeze'
        )