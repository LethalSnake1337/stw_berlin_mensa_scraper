from bs4 import BeautifulSoup
from datetime import date
from dataclasses import dataclass, field
from typing import List, Dict, Optional

@dataclass
class Meal:
    category: str
    name: str
    notes: List[str] = field(default_factory=list)
    prices: Dict[str, float] = field(default_factory=dict)
    allergens: List[str] = field(default_factory=list)

@dataclass
class DayMenu:
    day: date
    meals: List[Meal] = field(default_factory=list)
    closed: bool = False


class STWBerlinDayParser:
    """
        Parser for https://www.stw.berlin/xhr/speiseplan-wochentag.html POST HTML snippets.

        Usage:
            parser = STWBerlinDayParser()
            daymenu = parser.parse_html(html_bytes, target_date=date(2025,10,31))
            # -> List[DayMenu] (usually length 1 for this endpoint)
    """

    def parse_html(self, html: bytes | str, target_date: Optional[date] = None) -> List[DayMenu]:
        # --- decode if bytes ---
        if isinstance(html, bytes):
            # detect encoding via BeautifulSoup (it uses chardet internally)
            soup = BeautifulSoup(html, "html.parser")
        else:
            soup = BeautifulSoup(html, "html.parser")

        meals: List[Meal] = []

        # --- extract date ---
        date_text = soup.select_one(".glyphicon-calendar + span")
        if date_text:
            # e.g. "Mittwoch, 29.10.2025"
            day_str = date_text.text.strip().split(",")[-1].strip()
            try:
                parsed_date = date.fromisoformat(
                    "-".join(reversed(day_str.split(".")))
                )
            except Exception:
                parsed_date = target_date or date.today()
        else:
            parsed_date = target_date or date.today()

        # --- detect "Kein Speiseplan" / "Kein Speisenangebot" ---
        page_text = soup.get_text(" ", strip=True).lower()
        if "kein speiseplan" in page_text or "kein speisenangebot" in page_text:
            # nothing to parse — closed day
            return [DayMenu(day=parsed_date, meals=[], closed=True)]

        # --- loop over category groups ---
        for group in soup.select(".splGroupWrapper"):
            category = group.select_one(".splGroup")
            category_name = category.get_text(strip=True) if category else "Unbekannt"

            for meal_div in group.select(".splMeal"):
                name_el = meal_div.select_one(".bold")
                if not name_el:
                    continue

                name = name_el.get_text(strip=True)

                # --- prices ---
                price_el = meal_div.select_one(".col-md-3.text-right")
                prices = {}
                if price_el and "€" in price_el.text:
                    price_str = price_el.text.strip().replace("€", "")
                    parts = [p.strip().replace(",", ".") for p in price_str.split("/")]
                    if len(parts) >= 3:
                        try:
                            prices = {
                                "student": float(parts[0]),
                                "employee": float(parts[1]),
                                "other": float(parts[2]),
                            }
                        except ValueError:
                            pass

                # --- allergens ---
                allergens = []
                for tr in meal_div.select(".tooltip_content tr"):
                    cols = [td.get_text(strip=True) for td in tr.find_all("td")]
                    if len(cols) == 2:
                        allergens.append(f"Allergens: {cols[0]} {cols[1]}")

                # --- notes from icons ---
                notes = []
                for img in meal_div.select(".splIcon"):
                    alt = img.get("alt")
                    if alt:
                        clean = BeautifulSoup(alt, "html.parser").get_text(" ").strip()
                        notes.append(clean)

                notes.extend(allergens)

                meals.append(Meal(
                    category=category_name,
                    name=name,
                    prices=prices,
                    allergens=allergens,
                    notes=notes,
                ))

        return [DayMenu(day=parsed_date, meals=meals, closed=(len(meals) == 0))]
