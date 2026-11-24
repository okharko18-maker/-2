
"""Лабораторна PP-LAB02. Варіант 13: Оренда авто."""

import csv
import json
import math
import sys
from pathlib import Path
from io import StringIO


FIELDS = ["brand", "klass", "days", "price_per_day", "insurance"]
CSV_FIELDS = FIELDS + ["total"]
CLASSES = ("економ", "комфорт", "бізнес")


def clean_record(raw: dict) -> dict | str:
    """Перевіряє та очищує один запис."""
    brand = str(raw.get("brand") or "").strip()
    klass = str(raw.get("klass") or "").strip().lower()
    days_text = str(raw.get("days") or "").strip()
    price_text = str(raw.get("price_per_day") or "").strip()
    insurance_text = str(raw.get("insurance") or "").strip().lower()

    if not brand:
        return "Порожнє поле brand"

    if klass not in CLASSES:
        return "Поле klass має бути одним із: економ, комфорт, бізнес"

    try:
        days = int(days_text)
    except (ValueError, TypeError):
        return "Поле days має бути цілим числом від 1 до 60"

    if not 1 <= days <= 60:
        return "Поле days має бути цілим числом від 1 до 60"

    try:
        price = float(price_text)
    except (ValueError, TypeError):
        return "Поле price_per_day має бути числом більше 0"

    if not math.isfinite(price) or price <= 0:
        return "Поле price_per_day має бути числом більше 0"

    if insurance_text not in ("так", "ні"):
        return "Поле insurance має бути «так» або «ні»"

    insurance = insurance_text == "так"
    total = round(days * price * (1.1 if insurance else 1), 2)

    return {
        "brand": brand,
        "klass": klass,
        "days": days,
        "price_per_day": price,
        "insurance": insurance,
        "total": total,
    }


def load_csv(path: str) -> tuple[list[dict], list[str]]:
    """Зчитує CSV-файл та перевіряє записи."""
    records = []
    errors = []

    with open(path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)

        if reader.fieldnames != FIELDS:
            return [], ["Помилка: некоректний заголовок"]

        row_number = 0

        for raw in reader:
            if not any(str(value or "").strip() for value in raw.values()):
                continue

            row_number += 1
            result = clean_record(raw)

            if isinstance(result, str):
                errors.append(f"Рядок {row_number}: {result}")
            else:
                records.append(result)

    return records, errors


def to_json_text(records: list[dict]) -> str:
    """Перетворює записи на JSON."""
    return json.dumps(
        {"records": records},
        indent=2,
        ensure_ascii=False
    )


def from_json_text(text: str) -> list[dict]:
    """Відновлює записи з JSON."""
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        raise ValueError("Некоректний JSON") from None

    if not isinstance(data, dict) or not isinstance(data.get("records"), list):
        raise ValueError("Відсутній ключ records")

    records = data["records"]

    for record in records:
        for field in FIELDS:
            if not isinstance(record, dict) or field not in record:
                raise ValueError(f"Відсутнє поле {field}")

    return records


def to_csv_text(records: list[dict]) -> str:
    """Перетворює записи на CSV."""
    output = StringIO(newline="")

    writer = csv.DictWriter(
        output,
        fieldnames=CSV_FIELDS,
        lineterminator="\n"
    )

    writer.writeheader()

    for record in records:
        row = {
            "brand": record["brand"],
            "klass": record["klass"],
            "days": record["days"],
            "price_per_day": f"{float(record['price_per_day']):.2f}",
            "insurance": "так" if record["insurance"] else "ні",
            "total": f"{float(record['total']):.2f}",
        }

        writer.writerow(row)

    return output.getvalue()


def convert(src: str, dst: str) -> str:
    """Конвертує CSV у JSON або JSON у CSV."""
    source = Path(src)
    destination = Path(dst)
    extension = source.suffix.lower()

    if extension == ".csv":
        records, errors = load_csv(src)

        destination.write_text(
            to_json_text(records),
            encoding="utf-8"
        )

        read_count = len(records) + len(errors)

        return (
            f"Прочитано: {read_count}, "
            f"записано: {len(records)}, "
            f"пропущено: {len(errors)}"
        )

    if extension == ".json":
        records = from_json_text(
            source.read_text(encoding="utf-8")
        )

        destination.write_text(
            to_csv_text(records),
            encoding="utf-8"
        )

        return (
            f"Прочитано: {len(records)}, "
            f"записано: {len(records)}, "
            "пропущено: 0"
        )

    raise ValueError("Непідтримуваний формат")


def summarize(records: list[dict]) -> dict:
    """Підсумовує вартість оренди за класами авто."""
    groups = {}

    for record in records:
        klass = record["klass"]

        if klass not in groups:
            groups[klass] = []

        groups[klass].append(float(record["total"]))

    result = {}

    for klass, totals in groups.items():
        count = len(totals)
        total_sum = round(sum(totals), 2)

        result[klass] = {
            "count": count,
            "sum": total_sum,
            "mean": round(total_sum / count, 2),
        }

    return result


def main(argv):
    """Консольний запуск програми."""
    if len(argv) != 3:
        print("Використання: python lab_13.py <джерело> <призначення>")
        return

    try:
        print(convert(argv[1], argv[2]))
    except (ValueError, FileNotFoundError) as error:
        print(f"Помилка: {error}")


if __name__ == "__main__":
    main(sys.argv)

