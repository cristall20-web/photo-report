from app.report import generate_report

for title in [
    "Фотоотчет по общестроительным работам",
    "Фотоотчет по механическим системам",
    "Фотоотчет по электрическим системам",
    "Фотоотчет по слаботочным системам",
]:
    path = generate_report({
        "title": title,
        "report_date": "10.09.2026",
        "items": [
            {"object_name": "М7", "executor": "МК РУС ИНДАСТРИС",
             "description": "Монтаж панелей", "photo_path": None},
            {"object_name": "АБК", "executor": "КМТ",
             "description": "Перегородки", "photo_path": None},
        ],
    })
    print("Создан:", path)