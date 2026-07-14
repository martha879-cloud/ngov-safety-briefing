# scripts/sources.py

import requests

TIMEOUT = 20


def fetch_json(url):
    """공통 JSON 요청"""

    r = requests.get(
        url,
        timeout=TIMEOUT,
        headers={
            "User-Agent": "KOICA-NGO-Safety-Dashboard"
        }
    )

    r.raise_for_status()

    return r.json()
