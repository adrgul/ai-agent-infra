import sqlite3

conn = sqlite3.connect('chat_app.db')
cursor = conn.cursor()

cursor.execute('SELECT * FROM users WHERE user_id = 1')
columns = [description[0] for description in cursor.description]
row = cursor.fetchone()

print('User ID 1 adatai:')
print('-' * 50)
for col, val in zip(columns, row):
    print(f'{col:15}: {val}')

conn.close()
