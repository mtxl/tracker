import json
import os
import sys

# Чтобы Windows-консоль не падала на русских буквах
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

FILE = "tasks.json"


# ---------- 1. ЗАГРУЗКА И СОХРАНЕНИЕ ----------

def load_tasks():
    """Читает задачи. Если файла нет или он битый — возвращает пустой список."""
    if not os.path.exists(FILE):
        return []
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, OSError):
        return []


def save_tasks(tasks):
    """Сохраняет список задач в файл."""
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


# ---------- 2. ВЫВОД ----------

def show_tasks(tasks):
    """Печатает все задачи."""
    if not tasks:
        print("Задач нет.")
        return

    print("\n--- Задачи ---")
    for t in tasks:
        print(t["id"], ".", t["задача"], "-", t["исполнитель"], "-", t["статус"])
    print("--------------\n")


# ---------- 3. ДОБАВЛЕНИЕ ----------

def add_task(tasks):
    """Спрашивает данные и добавляет задачу."""
    название = input("Название задачи: ")
    исполнитель = input("Исполнитель: ")

    new_id = 1
    if tasks:
        new_id = max(t["id"] for t in tasks) + 1

    tasks.append({
        "id": new_id,
        "задача": название,
        "исполнитель": исполнитель,
        "статус": "новая"
    })

    print("Добавлено. Новая задача id =", new_id)


# ---------- 4. МЕНЮ ----------

def main():
    tasks = load_tasks()

    while True:
        print("1. Показать задачи")
        print("2. Добавить задачу")
        print("3. Выход")

        choice = input("Выбери: ")

        if choice == "1":
            show_tasks(tasks)
        elif choice == "2":
            add_task(tasks)
            save_tasks(tasks)
        elif choice == "3":
            save_tasks(tasks)
            print("Пока!")
            break
        else:
            print("Нет такого пункта.")


if __name__ == "__main__":
    main()
