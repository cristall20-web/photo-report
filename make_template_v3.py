# make_template_v3.py
from docx import Document
from docx.shared import Pt, Mm, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

LOGO_PATH = "app/templates/bovis_logo.png"

COMPANY_LINES = [
    "ООО «БОВИС УПРАВЛЕНИЕ ПРОЕКТАМИ»",
    "121059, г.Москва",
    "Вн. Тер. Г. Муниципальный округ Дорогомилово,",
    "ул. 1-я Бородинская, д. 2А, помещ. 3Ц",
]

COMPANY_COLOR = RGBColor(0x1A, 0x89, 0xC0)
COMPANY_FONT = "Arial Narrow"
COMPANY_SIZE = 9

PAGE_CONTENT_WIDTH = Cm(18)
LEFT_WIDTH = Cm(5)
RIGHT_WIDTH = PAGE_CONTENT_WIDTH - LEFT_WIDTH

ROW_HEIGHT_CM = 6


def set_default_style(doc, font_name="Arial", size=11):
    style = doc.styles["Normal"]
    style.font.name = font_name
    style.font.size = Pt(size)
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), font_name)


def add_field(paragraph, instr_text):
    run = paragraph.add_run()
    fldChar1 = OxmlElement("w:fldChar")
    fldChar1.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText")
    instrText.set(qn("xml:space"), "preserve")
    instrText.text = instr_text
    fldChar2 = OxmlElement("w:fldChar")
    fldChar2.set(qn("w:fldCharType"), "end")
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run.font.name = "Arial"
    run.font.size = Pt(11)


def remove_table_borders(table):
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for name in ("top", "left", "bottom", "right", "insideH", "insideV"):
        b = OxmlElement(f"w:{name}")
        b.set(qn("w:val"), "none")
        borders.append(b)
    tblPr.append(borders)


def set_row_height(row, height_cm):
    tr = row._tr
    trPr = tr.get_or_add_trPr()
    trHeight = OxmlElement("w:trHeight")
    trHeight.set(qn("w:val"), str(int(height_cm * 567)))
    trHeight.set(qn("w:hRule"), "atLeast")
    trPr.append(trHeight)


def set_cell_margins(cell, top=100, bottom=100, left=100, right=100):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement("w:tcMar")
    for name, val in (("top", top), ("bottom", bottom), ("left", left), ("right", right)):
        el = OxmlElement(f"w:{name}")
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        tcMar.append(el)
    tcPr.append(tcMar)


# ==========================
doc = Document()
set_default_style(doc, "Arial", 11)

section = doc.sections[0]
section.top_margin = Cm(1.5)
section.bottom_margin = Cm(1.5)
section.left_margin = Cm(1.5)
section.right_margin = Cm(1.5)

# ========== ВЕРХНИЙ КОЛОНТИТУЛ ==========
header = section.header
header.is_linked_to_previous = False
for p in header.paragraphs:
    p.clear()

h_table = header.add_table(rows=1, cols=2, width=Cm(18))
h_table.autofit = True

# Автоподбор по ширине окна: таблица 100%, колонки 30%/70%
tbl = h_table._tbl
tblPr = tbl.tblPr
tblW = OxmlElement("w:tblW")
tblW.set(qn("w:w"), "5000")
tblW.set(qn("w:type"), "pct")
tblPr.append(tblW)

# Пропорции колонок
for i, col in enumerate(h_table.columns):
    for cell in col.cells:
        tcPr = cell._tc.get_or_add_tcPr()
        tcW = OxmlElement("w:tcW")
        tcW.set(qn("w:w"), "3000" if i == 0 else "7000")
        tcW.set(qn("w:type"), "pct")
        tcPr.append(tcW)

# Логотип
left_cell = h_table.cell(0, 0)
left_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
left_cell.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.LEFT
if os.path.exists(LOGO_PATH):
    run = left_cell.paragraphs[0].add_run()
    run.add_picture(LOGO_PATH, width=Cm(3.5))
else:
    r = left_cell.paragraphs[0].add_run("[ЛОГОТИП]")
    r.font.name = "Arial"
    r.font.size = Pt(9)

# Адрес
right_cell = h_table.cell(0, 1)
right_cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
for i, line in enumerate(COMPANY_LINES):
    p = right_cell.paragraphs[0] if i == 0 else right_cell.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    run = p.add_run(line)
    run.font.name = COMPANY_FONT
    run.font.size = Pt(COMPANY_SIZE)
    run.font.color.rgb = COMPANY_COLOR
    rpr = run._r.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rfonts.set(qn(attr), COMPANY_FONT)

remove_table_borders(h_table)

# Отступ 6 пт после таблички шапки
after_header = header.add_paragraph()
after_header.paragraph_format.space_before = Pt(0)
after_header.paragraph_format.space_after = Pt(6)
after_header.paragraph_format.line_spacing = 1.0

# ========== НИЖНИЙ КОЛОНТИТУЛ ==========
footer = section.footer
footer.is_linked_to_previous = False
for p in footer.paragraphs:
    p.clear()

fp = footer.paragraphs[0]
fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = fp.add_run("Страница ")
run.font.name = "Arial"
run.font.size = Pt(11)
add_field(fp, "PAGE")
run = fp.add_run(" из ")
run.font.name = "Arial"
run.font.size = Pt(11)
add_field(fp, "NUMPAGES")

# ========== ЗАГОЛОВОК ==========
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.paragraph_format.space_before = Pt(0)
title.paragraph_format.space_after = Pt(3)
title.paragraph_format.line_spacing = 1.0

r1 = title.add_run("{{ title }}")
r1.bold = True
r1.font.name = "Arial"
r1.font.size = Pt(11)

r2 = title.add_run(" от ")
r2.bold = True
r2.font.name = "Arial"
r2.font.size = Pt(11)

r3 = title.add_run("{{ report_date }}")
r3.bold = True
r3.font.name = "Arial"
r3.font.size = Pt(11)

# ========== ТАБЛИЦА ДАННЫХ ==========
table = doc.add_table(rows=1, cols=2)
table.style = "Table Grid"
table.alignment = WD_TABLE_ALIGNMENT.CENTER
table.autofit = False
table.columns[0].width = LEFT_WIDTH
table.columns[1].width = RIGHT_WIDTH

for row in table.rows:
    row.cells[0].width = LEFT_WIDTH
    row.cells[1].width = RIGHT_WIDTH

set_row_height(table.rows[0], ROW_HEIGHT_CM)

left = table.cell(0, 0)
left.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
set_cell_margins(left)

p = left.paragraphs[0]
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(0)
p.paragraph_format.space_after = Pt(0)
run = p.add_run("{{ object_name }}")
run.bold = True
run.font.name = "Arial"
run.font.size = Pt(11)

p2 = left.add_paragraph()
p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
p2.paragraph_format.space_before = Pt(0)
p2.paragraph_format.space_after = Pt(0)
run = p2.add_run("{{ executor }}")
run.bold = True
run.font.name = "Arial"
run.font.size = Pt(11)

p3 = left.add_paragraph()
p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
p3.paragraph_format.space_before = Pt(0)
p3.paragraph_format.space_after = Pt(0)
run = p3.add_run("{{ description }}")
run.font.name = "Arial"
run.font.size = Pt(11)

right = table.cell(0, 1)
right.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
set_cell_margins(right)
rp = right.paragraphs[0]
rp.alignment = WD_ALIGN_PARAGRAPH.CENTER
rp.paragraph_format.space_before = Pt(0)
rp.paragraph_format.space_after = Pt(0)
rp.add_run("__PHOTO__")

doc.save("app/templates/report_template_v3.docx")
print("OK: шаблон v3 создан (с автоподбором таблицы в шапке)")