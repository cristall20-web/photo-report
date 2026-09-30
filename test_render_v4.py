from app.report import generate_report

path = generate_report({
    "title": "Фотоотчет по общестроительным работам",
    "report_date": "29.09.2026",
    "items": [
        {"object_name": "М7", "executor": "МК РУС ИНДАСТРИС", "description": "Монтаж стеновых сэндвич-панелей", "photo_path": None},
        {"object_name": "АБК", "executor": "КМТ", "description": "Устройство перегородок из ГКЛ", "photo_path": None},
        {"object_name": "М7.3", "executor": "СК МИР", "description": "Наружные сети В1 и К1", "photo_path": None},
        {"object_name": "ЭЦ-2", "executor": "ТЭЛМАС", "description": "Монтаж металлических ферм", "photo_path": None},
    ],
})
print("Файл создан:", path)