import argparse
import os
import shutil
from pathlib import Path
from time import sleep

from cafenero_parser import parse_cafenero_today
from fetcher import Fetcher
from loader import load_canteens_toml

from pyopenmensa.feed import LazyBuilder, BaseBuilder
from datetime import date, timedelta

from meta_data_builder import build_canteen_xml, pretty_xml
from parser import STWBerlinDayParser

url = "https://www.stw.berlin/xhr/speiseplan-wochentag.html"
url_mensa_list = "https://www.stw.berlin/mensen/"

parser = argparse.ArgumentParser()
parser.add_argument("--parse_meta_data", action="store_true", help="Run canteen metadata parser")
args = parser.parse_args()

if __name__ == '__main__':

    # Get current Date time
    today = date.today()
    fetcher = Fetcher()

    # check if start param is --parse_meta_data then only parse canteen meta data
    if args.parse_meta_data:
        if os.path.exists("meta"):
            shutil.rmtree("meta")

        os.makedirs("meta", exist_ok=True)
        for k, c in load_canteens_toml(Path("canteens.toml")).items():
            file_path = os.path.join("meta", f"{c.key}.xml")

            root = build_canteen_xml(c)
            xml_str = pretty_xml(root)
            out_path = Path(file_path)
            out_path.write_text(xml_str, encoding="utf-8")
            print(f"✅ Created {out_path.name}")
        # Call Parser
        exit(0)


    if os.path.exists("output"):
        shutil.rmtree("output")

    for k, c in load_canteens_toml(Path("canteens.toml")).items():
        # Create Loop to fetch each day from two weeks

        canteen = LazyBuilder()

        if "stw.berlin" in c.source:
            for day in range(0, 14):
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
                        print(f"  [{m.category}] {m.name}")
                        print(f"    Prices: {m.prices}")
                        print(f"    Allergens: {m.allergens}")
                        print(f"    Notes: {m.notes}")

                        if not getattr(m, "name", ""):
                            continue

                        canteen.addMeal(dm.day, m.category, m.name, m.notes, m.prices)

        elif "cafenero.net" in c.source:
            day_menus = parse_cafenero_today()
            for dm in day_menus:
                if dm.closed:
                    canteen.setDayClosed(dm.day)
                else:
                    for m in dm.meals:
                        canteen.addMeal(dm.day, m.category, m.name, m.notes, m.prices)

        xml_str = canteen.toXMLFeed()

        os.makedirs("output", exist_ok=True)
        file_path = os.path.join("output", f"{c.key}.xml")

        with open(file_path, "w") as f:
            f.write(xml_str)

        # Sleep to not get Rate limit
        sleep(10)


