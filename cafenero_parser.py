# cafenero_parser.py

import requests
from pdfminer.high_level import extract_text
from datetime import date
from typing import List
from io import BytesIO


from parser import Meal, DayMenu   # <- vorhandene Strukturen

PDF_URL = "https://cafenero.net/speisekarte.pdf"


def fetch_pdf_text() -> str:
    r = requests.get(PDF_URL, timeout=30)
    r.raise_for_status()

    pdf_bytes = r.content
    bio = BytesIO(pdf_bytes)

    # Wichtig: KEIN Keyword-Argument, einfach file-like obj übergeben
    text = extract_text(bio)

    return text

# ---------------------------------------------------------
# SAME cleaning logic as before (modified to work with text)
# ---------------------------------------------------------

def text_to_menu_list(text: str) -> List[str]:
    def clean(s):
        return " ".join(s.split()).replace(" €", "€")

    cleaned = []
    tmp = ""
    before_daily = True

    for line in text.splitlines():
        if "cafeneroinder" in line:
            continue

        if "mittagstisch" in line.lower():
            cleaned.append(clean(line))
            cleaned.append("")
        elif "---" in line:
            for i in line.split("---"):
                cleaned.append(clean(i))
        elif not line.strip():
            before_daily = False
        elif before_daily:
            cleaned.append(clean(line))
        else:
            tmp = f"{tmp} {line}"
            if any(tmp.strip().endswith(k) for k in ["€", "vegetarisch", "vegan", "fisch"]):
                cleaned.append(clean(tmp))
                tmp = ""

    if tmp.strip():
        cleaned.append(clean(tmp))

    return [x for x in cleaned if x.strip()]


# ---------------------------------------------------------
# Build DayMenu / Meal objects for OpenMensa builder
# ---------------------------------------------------------

def parse_cafenero_today() -> List[DayMenu]:
    text = fetch_pdf_text()
    lines = text_to_menu_list(text)

    meals = []
    category = "Mittagstisch"

    for line in lines:
        low = line.lower()

        if "mittagstisch" in low:
            category = line
            continue

        name = line
        notes = []
        prices = {}

        # extract price (simple)
        parts = name.rsplit(" ", 1)
        if len(parts) == 2 and parts[1].endswith("€"):
            price_raw = parts[1].replace("€", "").replace(",", ".")
            try:
                prices["other"] = float(price_raw)
                name = parts[0]
            except ValueError:
                pass

        # detect labels as notes
        for n in ["vegan", "vegetarisch", "fisch"]:
            if n in low:
                notes.append(n)

        meals.append(
            Meal(
                category=category,
                name=name,
                notes=notes,
                prices=prices,
                allergens=[],
            )
        )

    today = date.today()
    return [DayMenu(day=today, meals=meals, closed=(len(meals) == 0))]
