# test_render_v3.py
from app.report import generate_report

path = generate_report({
    "title": "Фотоотчет по общестроительным работам",
    "report_date": "29.09.2026",
    "items": [
        {"object_name": "М7", "executor": "МК Рус", "description": "Монтаж стеновых сэндвич-панелей", "photo_path": None},
        {"object_name": "АБК", "executor": "КМТ", "description": "Устройство перегородок из ГКЛ", "photo_path": None},
        {"object_name": "АБК 2", "executor": "КМТ", "description": "Наливной пол на 3 этаже", "photo_path": None},
    ],
})
print("Файл создан:", path)