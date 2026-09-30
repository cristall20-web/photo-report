import os
import re
import uuid
import shutil
from urllib.parse import quote, unquote
from typing import List

import httpx
from fastapi import FastAPI, UploadFile, File, Form, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app import models
from app.report import generate_report, convert_to_pdf

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Фотоотчёт")

UPLOAD_DIR = "uploads"
REPORTS_DIR = "reports"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

templates = Jinja2Templates(directory="app/templates")

LANGUAGETOOL_URL = "https://api.languagetool.org/v2/check"


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(request, "form.html", {})


@app.post("/upload-photo")
async def upload_photo(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".jpg", ".jpeg", ".png"):
        return {"error": "Только JPG/PNG"}

    filename = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(UPLOAD_DIR, filename)

    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {"path": path, "url": f"/uploads/{filename}"}


def _save_report_and_items(db, title, report_date, object_names,
                           executors, descriptions, photo_paths):
    report = models.Report(title=title, report_date=report_date)
    db.add(report)
    db.commit()
    db.refresh(report)

    items_data = []
    for i, (obj, ex, desc, photo) in enumerate(
        zip(object_names, executors, descriptions, photo_paths)
    ):
        db.add(models.ReportItem(
            report_id=report.id,
            object_name=obj,
            executor=ex,
            description=desc,
            photo_path=photo or None,
            order_num=i,
        ))
        items_data.append({
            "object_name": obj,
            "executor": ex,
            "description": desc,
            "photo_path": photo or None,
        })
    db.commit()
    return items_data


def _format_date(report_date: str) -> str:
    if not report_date:
        return ""
    try:
        y, m, d = report_date.split("-")
        return f"{d}.{m}.{y}"
    except ValueError:
        return report_date


@app.post("/generate")
async def generate(
    title: str = Form(...),
    report_date: str = Form(...),
    object_names: List[str] = Form(...),
    executors: List[str] = Form(...),
    descriptions: List[str] = Form(...),
    photo_paths: List[str] = Form(...),
    db: Session = Depends(get_db),
):
    items_data = _save_report_and_items(
        db, title, report_date, object_names, executors, descriptions, photo_paths
    )
    formatted_date = _format_date(report_date)

    docx_path = generate_report({
        "title": title,
        "report_date": formatted_date,
        "items": items_data,
    })

    download_name = os.path.basename(docx_path)
    encoded_name = quote(download_name, safe='')

    return {
        "download_url": f"/download/{encoded_name}",
        "filename": download_name,
    }


@app.post("/generate-pdf")
async def generate_pdf(
    title: str = Form(...),
    report_date: str = Form(...),
    object_names: List[str] = Form(...),
    executors: List[str] = Form(...),
    descriptions: List[str] = Form(...),
    photo_paths: List[str] = Form(...),
    db: Session = Depends(get_db),
):
    items_data = _save_report_and_items(
        db, title, report_date, object_names, executors, descriptions, photo_paths
    )
    formatted_date = _format_date(report_date)

    docx_path = generate_report({
        "title": title,
        "report_date": formatted_date,
        "items": items_data,
    })

    pdf_path = convert_to_pdf(docx_path)

    download_name = os.path.basename(pdf_path)
    encoded_name = quote(download_name, safe='')

    return {
        "download_url": f"/download/{encoded_name}",
        "filename": download_name,
    }


@app.get("/download/{encoded_filename}")
async def download_file(encoded_filename: str):
    filename = unquote(encoded_filename)
    file_path = os.path.join(REPORTS_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Файл не найден: {filename}")

    encoded = quote(filename, safe='')

    if filename.lower().endswith(".pdf"):
        media_type = "application/pdf"
    else:
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    return FileResponse(
        path=file_path,
        media_type=media_type,
        headers={
            "Content-Disposition": (
                f"attachment; "
                f"filename*=UTF-8''{encoded}; "
                f"filename=\"report\""
            )
        },
    )


# ==================== ПРОВЕРКА ОРФОГРАФИИ ====================

def _add_match(matches, offset, length, message, rule_id, replacement):
    """Хелпер: добавляет match."""
    matches.append({
        "offset": offset,
        "length": length,
        "message": message,
        "rule": {"id": rule_id, "description": message},
        "replacements": [{"value": replacement}],
    })


def _custom_rules_check(text: str) -> list:
    """Свои правила: точки, пробелы, знаки препинания."""
    matches = []

    # ======================================================
    # 1. Мусорные сочетания знаков препинания: ". ,", ", .", ". .", ", ," и т.д.
    # Ищем любые комбинации из 2+ знаков [.,;:!?] с пробелами и без.
    # Правило: если рядом стоят два разных знака — оставить только последний (или более логичный).
    # ======================================================

    # Сначала обрабатываем ". ," / ", ." / ". ." / ", ," / "; ." и т.п.
    # Комбинация: знак + пробелы + знак
    # Оставляем точку, если она есть; иначе — запятую; иначе — первый знак.
    sign_sequence_re = re.compile(r"([.,;:!?])\s*([.,;:!?])")
    for m in sign_sequence_re.finditer(text):
        first_sign = m.group(1)
        second_sign = m.group(2)

        # Если оба знака одинаковые — оставляем один
        if first_sign == second_sign:
            # ". ." → "." ; ", ," → ","
            replacement = first_sign
            _add_match(
                matches, m.start(), m.end() - m.start(),
                f"Двойной знак «{first_sign}{second_sign}» — оставьте один",
                "CUSTOM_DOUBLE_SIGN", replacement,
            )
        else:
            # Разные знаки: ". ," → "," ; ", ." → "." ; "; ." → "." ; ". ;" → ";"
            # Логика: точка важнее запятой; точка с запятой важнее запятой;
            # если есть точка — оставляем её; иначе — второй знак.
            if "." in (first_sign, second_sign):
                replacement = "."
            elif ";" in (first_sign, second_sign):
                replacement = ";"
            elif ":" in (first_sign, second_sign):
                replacement = ":"
            elif "?" in (first_sign, second_sign):
                replacement = "?"
            elif "!" in (first_sign, second_sign):
                replacement = "!"
            else:
                replacement = second_sign

            _add_match(
                matches, m.start(), m.end() - m.start(),
                f"Недопустимое сочетание знаков «{first_sign} {second_sign}» — оставьте «{replacement}»",
                "CUSTOM_MIXED_SIGNS", replacement,
            )

    # ======================================================
    # 2. Две и более точек подряд
    # ======================================================
    for m in re.finditer(r"\.{2,}", text):
        start = m.start()
        end = m.end()
        after = text[end:]
        is_at_end = after.strip() == ""

        if not is_at_end:
            _add_match(
                matches, start, end - start,
                "Многоточие посреди предложения — замените на пробел",
                "CUSTOM_DOTS_MIDDLE", " ",
            )
        else:
            if end - start > 1:
                _add_match(
                    matches, start, end - start,
                    "Лишние точки в конце — оставьте одну",
                    "CUSTOM_DOTS_END", ".",
                )

    # ======================================================
    # 3. Точка/запятая перед открывающей скобкой или внутри "(футляра.трубы"
    # Точка внутри слова (между буквами) — заменить на пробел.
    # Например: "футляра.трубы" → "футляра трубы"
    # ======================================================
    for m in re.finditer(r"([А-Яа-яЁёA-Za-z])\.([А-Яа-яЁёA-Za-z])", text):
        _add_match(
            matches, m.start() + 1, 1,
            "Точка внутри слова — замените на пробел",
            "CUSTOM_DOT_INSIDE_WORD", " ",
        )

    # ======================================================
    # 4. Точка/запятая непосредственно перед закрывающей скобкой или после открывающей
    # Например: ".)." или "(. "
    # ======================================================
    # ". )" → ")" ; ". )" с пробелами → ")"
    for m in re.finditer(r"([.,;:!?])\s*\)", text):
        _add_match(
            matches, m.start(), m.end() - m.start(),
            "Знак препинания перед закрывающей скобкой — уберите",
            "CUSTOM_PUNCT_BEFORE_PAREN", ")",
        )
    # "(." → "("
    for m in re.finditer(r"\(\s*([.,;:!?])", text):
        _add_match(
            matches, m.start(), m.end() - m.start(),
            "Знак препинания после открывающей скобки — уберите",
            "CUSTOM_PUNCT_AFTER_PAREN", "(",
        )

    # ======================================================
    # 5. Пробел перед знаком препинания
    # ======================================================
    for m in re.finditer(r"\s+([.,!?;:])", text):
        _add_match(
            matches, m.start(), m.end() - m.start(),
            "Лишний пробел перед знаком препинания",
            "CUSTOM_SPACE_BEFORE_PUNCT", m.group(1),
        )

    # ======================================================
    # 6. Двойные пробелы
    # ======================================================
    for m in re.finditer(r"  +", text):
        _add_match(
            matches, m.start(), m.end() - m.start(),
            "Двойной пробел",
            "CUSTOM_DOUBLE_SPACE", " ",
        )

    # ======================================================
    # 7. Нет пробела после знака препинания (кроме чисел и точки в числах)
    # ======================================================
    for m in re.finditer(r"([,;:!?])(?=[^\s\d])", text):
        # запятая, ;, :, !, ? — без пробела после
        _add_match(
            matches, m.start(), 1,
            "Нет пробела после знака препинания",
            "CUSTOM_NO_SPACE_AFTER_PUNCT", m.group(1) + " ",
        )

    # Отдельно для точки: точка + буква → точка + пробел
    # Но не трогаем числа: 1.5, 12.09.2026
    for m in re.finditer(r"\.(?=[А-Яа-яЁёA-Za-z])", text):
        # проверяем, что слева тоже буква (не цифра)
        before = text[max(0, m.start() - 1):m.start()]
        if before and not before.isdigit():
            _add_match(
                matches, m.start(), 1,
                "Нет пробела после точки",
                "CUSTOM_NO_SPACE_AFTER_DOT", ". ",
            )

    # ======================================================
    # 8. Точка или запятая сразу после открывающей/перед закрывающей кавычкой
    # ======================================================
    # ")." → ") "
    for m in re.finditer(r"\)([.,;:!?])", text):
        _add_match(
            matches, m.start() + 1, 1,
            "Знак препинания сразу после закрывающей скобки — уберите",
            "CUSTOM_PUNCT_AFTER_PAREN_CLOSE", "",
        )

    return matches


def _merge_matches(lt_matches: list, custom_matches: list) -> list:
    """Объединяет ошибки LanguageTool и наши правила, убирая пересечения."""
    all_matches = list(custom_matches) + list(lt_matches)
    all_matches.sort(key=lambda m: m.get("offset", 0))

    result = []
    last_end = -1
    for m in all_matches:
        start = m.get("offset", 0)
        length = m.get("length", 0)
        if start >= last_end:
            result.append(m)
            last_end = start + length
    return result


@app.post("/spell-check")
async def spell_check(payload: dict):
    """Прокси к LanguageTool + свои правила."""
    text = payload.get("text", "")
    language = payload.get("language", "ru-RU")

    if not text or len(text) > 20000:
        return {"matches": []}

    custom_matches = _custom_rules_check(text)

    lt_matches = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                LANGUAGETOOL_URL,
                data={"text": text, "language": language},
            )
            response.raise_for_status()
            data = response.json()
            lt_matches = data.get("matches", [])
    except Exception as e:
        print(f"LanguageTool error: {e}")

    combined = _merge_matches(lt_matches, custom_matches)
    return {"matches": combined}


app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")