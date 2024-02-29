class StaffPerson:
    def __init__(self, id: int, admin = False, credit_change = 100) -> None:
        self.id = id
        self.admin = admin
        self.credit_change = credit_change


import sqlite3
from abc import ABC, abstractmethod
from typing import List

class ITGStaffPersonRepository(ABC):
    @abstractmethod
    def add(self, staff: StaffPerson) -> None:
        pass

    @abstractmethod
    def get_by_id(self, id: int):
        pass

    @abstractmethod
    def get_all(self) -> List[StaffPerson]:
        pass

    @abstractmethod
    def update(self, staff) -> None:
        pass

    @abstractmethod
    def delete(self, id: int) -> None:
        pass


class TGStaffPersonRepository(ITGStaffPersonRepository):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._create_table()
        #self.add(StaffPerson(788237639, True, -1))

    def _create_table(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS staff (
                tg_id INTEGER PRIMARY KEY,
                admin BOOLEAN NOT NULL,
                credit_change INTEGER DEFAULT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def add(self, staff) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Перевірка, чи не існує вже такого tg_id
        cursor.execute('SELECT tg_id FROM staff WHERE tg_id = ?', (staff.id,))
        existing_record = cursor.fetchone()
        if existing_record:
            print(f"Record with tg_id {staff.id} already exists.")
            conn.close()
            return

        # Вставка нового запису
        cursor.execute('''
            INSERT INTO staff (tg_id, admin, credit_change)
            VALUES (?, ?, ?)
        ''', (staff.id, staff.admin, staff.credit_change if staff.admin else None))
        conn.commit()
        conn.close()

    def get_by_id(self, id: int):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM staff WHERE tg_id = ?', (id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return StaffPerson(*row)

    def get_all(self) -> List[StaffPerson]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM staff')
        rows = cursor.fetchall()
        conn.close()
        return [StaffPerson(*row) for row in rows]

    def update(self, staff) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE staff
            SET admin = ?, credit_change = ?
            WHERE tg_id = ?
        ''', (staff.admin, staff.credit_change, staff.id))
        conn.commit()
        conn.close()

    def delete(self, id: int) -> None:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM staff WHERE tg_id = ?', (id,))
        conn.commit()
        conn.close()

repo_staff = TGStaffPersonRepository('data/staff.db')