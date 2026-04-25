import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'blog.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('PRAGMA table_info(blogs)')
columns = cursor.fetchall()
print('Current blogs table columns:')
for col in columns:
    print(f'  {col}')

has_is_published = any(col[1] == 'is_published' for col in columns)
print(f'\nis_published column exists: {has_is_published}')

if not has_is_published:
    try:
        cursor.execute('ALTER TABLE blogs ADD COLUMN is_published INTEGER DEFAULT 0')
        conn.commit()
        print('Successfully added is_published column')
    except Exception as e:
        print(f'Failed to add column: {e}')
else:
    print('is_published column already exists')

conn.close()
