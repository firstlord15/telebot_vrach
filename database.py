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
            phone_number TEXT,
            Admin TEXT
        )
    ''')

    conn.commit()
    conn.close()

def save_user_to_database(user_id, username, full_name, formatted_phone_number):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (user_id, username, full_name, phone_number) VALUES (?, ?, ?, ?)', (user_id, username, full_name, formatted_phone_number))

    conn.commit()
    conn.close()


def get_user_full_name_from_database(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('SELECT full_name FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    conn.close()
    return result[0] if result else None


def user_exists_in_database(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('SELECT user_id FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()

    conn.close()
    return result is not None

def add_patient_to_database(fullname, age, phone_number):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Создание таблицы Patients, если она еще не существует
    create_table_query = """CREATE TABLE IF NOT EXISTS patients (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                fullname TEXT NOT NULL,
                                age INTEGER,
                                phone_number TEXT,
                                Token TEXT
                            );"""
    cursor.execute(create_table_query)

    # Вставка данных пациента в таблицу
    cursor.execute('INSERT INTO patients (fullname, age, phone_number) VALUES (?, ?, ?)',
                   (fullname, age, phone_number))

    conn.commit()
    conn.close()

def get_all_patients_from_database():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute("SELECT * FROM patients")
    patients = [
        {"id": row[0], "fullname": row[1], "age": row[2], "phone_number": row[3]}
        for row in cur.fetchall()
    ]

    conn.close()
    
    return patients

def get_patient_from_database(patient_id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute("SELECT * FROM patients WHERE id=?", (patient_id,))
    row = cur.fetchone()

    if row:
        patient = {"id": row[0], "fullname": row[1], "age": row[2], "phone_number": row[3]}
    else:
        patient = None

    conn.close()

    return patient


if __name__ == '__main__':
    create_users_table()
