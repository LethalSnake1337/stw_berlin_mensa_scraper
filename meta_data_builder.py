from dataclasses import dataclass
from pathlib import Path
from typing import Dict
import tomllib  # Python 3.11+
import xml.etree.ElementTree as ET
from xml.dom import minidom

# --- XML constants ---
NS  = "http://openmensa.org/open-mensa-v2"
XSI = "http://www.w3.org/2001/XMLSchema-instance"
SCHEMA_LOC = f"{NS} {NS}.xsd"

ET.register_namespace('', NS)
ET.register_namespace('xsi', XSI)

DEFAULT_SCHEDULE = {
    "dayOfMonth": "*",
    "dayOfWeek": "*",
    "hour": "7,9",
    "minute": "10",
    "retry": "65 1 1440"
}


# --- Data Model ---
@dataclass
class CanteenMeta:
    key: str
    name: str
    street: str
    city: str
    id: int
    url: str
    source: str


def load_canteens_toml(path: Path) -> Dict[str, CanteenMeta]:
    """Load canteen definitions from TOML file into dataclasses."""
    data = tomllib.loads(path.read_bytes().decode())
    canteens = {}
    for key, val in data.get("canteens", {}).items():
        canteens[key] = CanteenMeta(
            key=key,
            name=val["name"],
            street=val["street"],
            city=val["city"],
            id=int(val["id"]),
            url=val["url"],
            source=val["source"],
        )
    return canteens


# --- XML Builder ---
def _sub(parent: ET.Element, tag: str, text: str | None):
    """Create a subelement only if text is not empty."""
    if not text:
        return
    el = ET.SubElement(parent, f"{{{NS}}}{tag}")
    el.text = str(text)


def build_canteen_xml(c: CanteenMeta) -> ET.Element:
    """Build <openmensa> XML for a single canteen."""
    root = ET.Element(f"{{{NS}}}openmensa", {
        "version": "2.1",
        f"{{{XSI}}}schemaLocation": SCHEMA_LOC,
    })

    canteen = ET.SubElement(root, f"{{{NS}}}canteen")

    _sub(canteen, "name", c.name)
    _sub(canteen, "address", c.street)
    _sub(canteen, "city", c.city)

    if c.url:
        feed = ET.SubElement(canteen, f"{{{NS}}}feed", {"name": "full"})
        ET.SubElement(feed, f"{{{NS}}}schedule", DEFAULT_SCHEDULE)
        _sub(feed, "url", c.url)
        _sub(feed, "source", c.source)

    return root


def pretty_xml(element: ET.Element) -> str:
    rough = ET.tostring(element, encoding="utf-8", xml_declaration=True)
    return minidom.parseString(rough).toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")
