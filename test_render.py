from docxtpl import DocxTemplate
t = DocxTemplate('app/templates/report_template.docx')
t.render({
    'title': 'ТЕСТ',
    'report_date': '29.09.2026',
    'address': 'Адрес',
    'items': [
        {'object_name': 'М7', 'executor': 'МК Рус', 'description': 'Описание', 'photo': None}
    ],
    'generated_at': 'сейчас',
})
t.save('reports/TEST_FINAL.docx')
print('OK: файл создан')