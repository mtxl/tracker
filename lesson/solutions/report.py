#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""report.py — сводка по задачам и проверка качества данных.

Только стандартная библиотека. Python 3.8+.

Запуск:
    python3 report.py
    python3 report.py tasks.json report.csv

Код возврата:
    0 — ошибок в данных нет;
    1 — найдены ошибки качества данных;
    2 — не удалось прочитать файл.
"""

import csv
import json
import sys
from collections import Counter
from pathlib import Path

# Чтобы Windows-консоль не падала на русских буквах
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REQUIRED_FIELDS = ("id", "задача", "исполнитель", "статус")

# Разные написания статуса -> каноническое значение
STATUS_ALIASES = {
    "новая": "новая",
    "новый": "новая",
    "в работе": "в работе",
    "вработе": "в работе",
    "готово": "готово",
    "готова": "готово",
    "готов": "готово",
    "сделано": "готово",
    "выполнено": "готово",
    "закрыта": "готово",
    "закрыто": "готово",
}

STATUS_ORDER = ("новая", "в работе", "готово")


def normalize_status(value):
    """Приводит статус к каноническому виду или возвращает None."""
    if not isinstance(value, str):
        return None
    key = value.strip().casefold().replace("ё", "е")
    return STATUS_ALIASES.get(key)


def check_record(record, index, seen_ids):
    """Проверяет одну запись.

    Возвращает (errors, warnings, status_norm):
      errors   — проблемы, из-за которых запись нельзя считать;
      warnings — проблемы, которые исправляются автоматически;
      status_norm — канонический статус или None.
    """
    errors = []
    warnings = []

    if not isinstance(record, dict):
        return ["запись не является объектом"], warnings, None

    for field in REQUIRED_FIELDS:
        if field not in record:
            errors.append("нет поля '%s'" % field)

    raw_id = record.get("id")
    if "id" in record:
        if isinstance(raw_id, bool) or not isinstance(raw_id, int):
            errors.append(
                "id должен быть целым числом, а не %s" % type(raw_id).__name__
            )
        elif raw_id <= 0:
            errors.append("id должен быть больше 0")
        elif raw_id in seen_ids:
            errors.append(
                "id=%s уже встречался в записи №%s" % (raw_id, seen_ids[raw_id])
            )
        else:
            seen_ids[raw_id] = index

    for field in ("задача", "исполнитель"):
        if field in record:
            value = record[field]
            if not isinstance(value, str):
                errors.append("поле '%s' должно быть строкой" % field)
            elif not value.strip():
                errors.append("поле '%s' пустое" % field)

    status_norm = None
    if "статус" in record:
        raw_status = record["статус"]
        if not isinstance(raw_status, str):
            errors.append("поле 'статус' должно быть строкой")
        else:
            status_norm = normalize_status(raw_status)
            if status_norm is None:
                errors.append("неизвестный статус: '%s'" % raw_status)
            elif raw_status != status_norm:
                warnings.append(
                    "статус '%s' приведён к '%s'" % (raw_status, status_norm)
                )

    return errors, warnings, status_norm


def load_tasks(path):
    """Читает JSON-файл со списком задач."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("ожидался JSON-массив задач")
    return data


def main(argv):
    src = Path(argv[1]) if len(argv) > 1 else Path("tasks.json")
    dst = Path(argv[2]) if len(argv) > 2 else Path("report.csv")

    try:
        records = load_tasks(src)
    except FileNotFoundError:
        print("Ошибка: файл не найден:", src)
        return 2
    except json.JSONDecodeError as exc:
        print("Ошибка: файл не является корректным JSON:", exc)
        return 2
    except (OSError, ValueError) as exc:
        print("Ошибка чтения:", exc)
        return 2

    seen_ids = {}
    rows = []
    good = []
    error_records = 0
    warning_count = 0

    for index, record in enumerate(records, 1):
        errors, warnings, status_norm = check_record(record, index, seen_ids)

        if errors:
            error_records += 1
        else:
            good.append((record, status_norm))
        warning_count += len(warnings)

        rows.append(
            {
                "id": record.get("id", "") if isinstance(record, dict) else "",
                "задача": record.get("задача", "") if isinstance(record, dict) else "",
                "исполнитель": (
                    record.get("исполнитель", "") if isinstance(record, dict) else ""
                ),
                "статус": record.get("статус", "") if isinstance(record, dict) else "",
                "статус_норм": status_norm or "",
                "проблемы": "; ".join(errors + warnings),
            }
        )

    # --- сводка ---
    print("=== Отчёт по задачам ===")
    print("Файл:", src)
    print("Всего записей:", len(records))
    print("С ошибками:", error_records)
    print("Предупреждений:", warning_count)
    print("Пригодных записей:", len(good))
    print()

    status_counts = Counter(status for _, status in good)
    print("По статусам (пригодные записи):")
    for status in STATUS_ORDER:
        print("  %s: %d" % (status, status_counts.get(status, 0)))
    print()

    assignee_counts = Counter(
        record["исполнитель"].strip() for record, _ in good
    )
    print("По исполнителям (пригодные записи):")
    for name, count in sorted(assignee_counts.items(), key=lambda item: (-item[1], item[0])):
        print("  %s: %d" % (name, count))
    print()

    # Самопроверка: сумма по статусам должна совпадать с числом пригодных записей
    if sum(status_counts.values()) != len(good):
        print("ВНИМАНИЕ: сумма по статусам не совпадает с числом записей!")
        print()

    # --- выгрузка ---
    try:
        with open(dst, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(
                ["id", "задача", "исполнитель", "статус", "статус_норм", "проблемы"]
            )
            for row in rows:
                writer.writerow(
                    [
                        row["id"],
                        row["задача"],
                        row["исполнитель"],
                        row["статус"],
                        row["статус_норм"],
                        row["проблемы"],
                    ]
                )
    except OSError as exc:
        print("Ошибка записи CSV:", exc)
        return 2

    print("CSV сохранён:", dst, "(разделитель ';', кодировка utf-8-sig)")

    if error_records:
        print("Итог: есть ошибки в данных — отчёт требует проверки.")
        return 1

    print("Итог: ошибок нет.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
