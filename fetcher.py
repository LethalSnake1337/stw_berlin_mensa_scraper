import requests

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.1 Safari/537.36",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Referer": "https://www.stw.berlin/mensen/mensa-tu-hardenbergstrasse.html",
    "Origin": "https://www.stw.berlin",
    "X-Requested-With": "XMLHttpRequest",
}

class Fetcher:
    def __init__(self, timeout: int = 30):
        self.session = requests.Session()
        self.timeout = timeout

    def get(self, url: str) -> bytes:
        r = self.session.get(url, timeout=self.timeout)
        r.raise_for_status()
        return r.content

    def post(self, url: str, data: dict) -> bytes:
        r = self.session.post(url, data=data, timeout=self.timeout, headers=headers)
        r.raise_for_status()
        return r.content

if __name__ == "__main__":
    fetcher = Fetcher()
    html_bytes = fetcher.post(
        "https://www.stw.berlin/xhr/speiseplan-wochentag.html",
        {
            "resources_id": "321",
            "date": "2025-10-28"
        }
    )
    print(html_bytes.decode())