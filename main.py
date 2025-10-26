from pathlib import Path

from fetcher import Fetcher
from loader import load_canteens_toml

from pyopenmensa.feed import LazyBuilder, BaseBuilder
from datetime import date, timedelta

from parser import STWBerlinDayParser

url = "https://www.stw.berlin/xhr/speiseplan-wochentag.html"

def print_hi():
    canteen = LazyBuilder()
    canteen.addMeal(
        date(2024, 10, 31),
        "Hauptgericht",
        "Gulasch",
        notes= ["Mit Süßstoff", "Mit Schwein"],
        prices={"student": "1,15€", "other": "1,42€"}
    )
    print(canteen.toXMLFeed())


if __name__ == '__main__':
    # Get current Date time
    today = date.today()
    fetcher = Fetcher()
    for k, c in load_canteens_toml(Path("canteens.toml")).items():
        # Create Loop to fetch each day from two weeks

        canteen = LazyBuilder()

        for day in range(0, 15):
            print(today)
            print(today + timedelta(days=day))
            # Fetch speiseplan for currentDay
            html_bytes = fetcher.post(
                url,
                {
                    "resources_id": c.id,
                    "date": today + timedelta(days=day),
                }
            )

            # Call Parser
            parser = STWBerlinDayParser()
            daymenus = parser.parse_html(html_bytes, today)
            for dm in daymenus:
                print(f"Date: {dm.day}")
                if dm.closed:
                    canteen.setDayClosed(dm.day)
                for m in dm.meals:
                    #print(f"  [{m.category}] {m.name}")
                    #print(f"    Prices: {m.prices}")
                    #print(f"    Allergens: {m.allergens}")
                    #print(f"    Notes: {m.notes}")
                    canteen.addMeal(dm.day, m.category, m.name, m.notes, m.prices)

        canteen.toXMLFeed()


        #
        print(f"{c.id:3} | {c.name:30} | {c.city}")


