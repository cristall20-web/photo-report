from app.report import generate_report

generate_report({
    "title": "Фотоотчет по электрическим системам",
    "report_date": "25.09.2026",
    "items": [
        {"object_name": "М7.1", "executor": "ТИЕКТА",
         "description": "тест", "photo_path": None},
    ],
})
print("ЭОМ создан")