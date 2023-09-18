from pydrive.auth import GoogleAuth
import os

def authenticate():
    gauth = GoogleAuth(settings_file='settings.yaml')

    # Если существует файл с сохраненными ключами авторизации, просто загрузите его.
    if os.path.isfile('token.json'):
        gauth.LoadCredentialsFile('token.json')
        print('System: You are already authenticated!')

    # Если файла с сохраненными ключами авторизации нет, запустите процесс авторизации.
    if gauth.credentials is None:
        gauth.LocalWebserverAuth()
        print("System: You are not authenticated, let's do it!")

    # Обновите токены авторизации, если они истекли.
    elif gauth.access_token_expired:
        gauth.Refresh()
        print('System: You are authenticated again!')

    # В противном случае сохраните текущие ключи авторизации.
    else:
        gauth.Authorize()
        print('System: You are already authenticated!')

    gauth.SaveCredentialsFile('token.json')
    return gauth
