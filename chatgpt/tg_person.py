import sqlite3

class TGPerson:
    def __init__(self, id: str, name: str, pronouns: list, bio: str) -> None:
        self.id = id
        self.name = name
        self.pronouns = pronouns
        self.bio = bio

    def set_pronouns(self, list_str: list):
        self.pronouns = list_str

    def set_bio(self, bio_str: str):
        self.bio = bio_str

        

class TGPersonRepository:
    def __init__(self, db_path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS persons (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                pronouns TEXT NOT NULL,
                bio TEXT NOT NULL)
        """)
        #cursor.execute('INSERT INTO persons (id, name, pronouns, bio) VALUES (?, ?, ?, ?)', ('788237639', 'Максимка', 'ти/він', 'Розробник на C++. люблю low-level програмування'))
        conn.commit()

    def connect(self):
        return sqlite3.connect(self.db_path)

    def add_person(self, person: TGPerson):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO persons (id, name, pronouns, bio) VALUES (?, ?, ?, ?)',
                       (person.id, person.name, ','.join(person.pronouns), person.bio))
        conn.commit()
        conn.close()

    def update_person(self, person: TGPerson):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute('UPDATE persons SET name = ?, pronouns = ?, bio = ? WHERE id = ?',
                       (person.name, ','.join(person.pronouns), person.bio, person.id))
        conn.commit()
        conn.close()

    def get_person(self, id: str):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, pronouns, bio FROM persons WHERE id = ?', (id,))
            row = cursor.fetchone()
            if row:
                return TGPerson(row[0], row[1], row[2].split(','), row[3])
            return None
        
    def get_all_person_names(self):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM persons')
            names = cursor.fetchall()
            # Перетворюємо список імен в рядок
            names_str = str([name[0] for name in names])
            return names_str 
            # Результатом буде рядок, 
            # що містить візуальне представлення списку, 
            # наприклад: "['Максим', 'Олена', 'Іван']".
        
    def get_person_by_name(self, name: str):
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, pronouns, bio FROM persons WHERE name = ? LIMIT 1', (name,))
            row = cursor.fetchone()
            if row:
                return TGPerson(row[0], row[1], row[2].split(','), row[3])
            return None
