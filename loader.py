from dataclasses import dataclass
from pathlib import Path
from typing import Dict
import tomllib  # Python 3.11+

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
