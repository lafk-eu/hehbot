import sys
import asyncio
from hehbot import repo_user, repo_staff, Person, StaffPerson

class PersonNotFound(Exception):
    pass

async def add_admin_by_name(name: str):
    try:
        # Пошук персони за іменем в базі користувачів
        person = repo_user.by_name(name)
        if person is None:
            raise PersonNotFound(f"Person with name {name} not found.")
        
        # Створення нового об'єкта StaffPerson як адміністратор
        new_admin = StaffPerson(id=person.id, admin=True)
        
        # Додавання адміністратора в базу staff
        repo_staff.add(new_admin)
        print(f"Person {name} added as admin successfully.")
    except PersonNotFound as e:
        print(e)
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: script.py <name>")
        sys.exit(1)

    name = sys.argv[1]
    asyncio.run(add_admin_by_name(name))