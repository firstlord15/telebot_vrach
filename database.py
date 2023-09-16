import sqlite3
import json

def create_users_table():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            phone_number TEXT  
        )
    ''')

    conn.commit()
    conn.close()

def create_super_user_table():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS super_users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            phone_number TEXT
        )
    ''')

    conn.commit()
    conn.close()


def set_verification_status(user_id, status):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('UPDATE users SET is_verified = ? WHERE user_id = ?', (status, user_id))
    conn.commit()
    conn.close()

def is_verified(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('SELECT is_verified FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    conn.close()

    return bool(result[0]) if result else False


def save_user_to_database(user_data, platform_urls):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    user_id = user_data['user_id']
    username = user_data['username']
    name = user_data['name']
    platforms = user_data['platforms']
    
    # Создаем словарь для хранения готовых ссылок
    platform_links = {}
    for platform, social_media_id in platforms.items():
        if platform in platform_urls:
            platform_link = platform_urls[platform].format(social_media_id)
            platform_links[platform] = platform_link
    
    # Преобразуем словарь готовых ссылок в JSON-строку
    platform_links_json = json.dumps(platforms)

    cursor.execute('INSERT INTO users (user_id, username, name, platforms) VALUES (?, ?, ?, ?)',
                   (user_id, username, name, platform_links_json))

    conn.commit()
    conn.close()

# def get_links_from_database(user_id):
#     conn = sqlite3.connect('database.db')
#     cursor = conn.cursor()

#     cursor.execute('SELECT platforms FROM users WHERE user_id = ?', (user_id,))
#     platforms_data = cursor.fetchone()[0]

#     conn.close()

#     platforms = json.loads(platforms_data)
#     links = [{'text': platform, 'url': url} for platform, url in platforms.items()]
#     return links

def get_user_alias_from_database(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('SELECT name FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    conn.close()

    return result[0] if result else None

def get_user_data_from_database(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('SELECT username, name, platforms FROM users WHERE user_id = ?', (user_id,))
    user_data = cursor.fetchone()

    conn.close()

    if user_data is not None:
        username, name, platforms_data = user_data
        platforms = json.loads(platforms_data)
        return {
            'username': username,
            'name': name,
            'platforms': platforms
        }
    else:
        return None

def update_platform_url_in_database(user_id, platform, platform_url):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('SELECT platforms FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    if result is not None:
        platforms_data = result[0]
        platforms_dict = json.loads(platforms_data)
        
        platforms_dict[platform] = platform_url
        updated_platforms_data = json.dumps(platforms_dict)

        cursor.execute('UPDATE users SET platforms = ? WHERE user_id = ?', (updated_platforms_data, user_id))
        conn.commit()
    
    conn.close()



def save_updated_profile_data(user_id, name, platforms, platform_urls):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('SELECT platforms FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    if result is not None:
        platforms_data = result[0]
        platforms_dict = json.loads(platforms_data)

        for platform, social_media_id in platforms.items():
            if platform in platform_urls:
                platform_link = platform_urls[platform].format(social_media_id)
                platforms_dict[platform] = platform_link

        updated_platforms_data = json.dumps(platforms_dict)

        cursor.execute('UPDATE users SET name = ?, platforms = ? WHERE user_id = ?', (name, updated_platforms_data, user_id))
        conn.commit()
    
    conn.close()


def update_user_name_in_database(user_id, new_name):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('UPDATE users SET name = ? WHERE user_id = ?', (new_name, user_id))
    conn.commit()
    conn.close()

def user_exists_in_database(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    conn.close()

    return result is not None

if __name__ == '__main__':
    create_users_table()
    create_super_user_table()
