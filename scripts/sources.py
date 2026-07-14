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
USGS_URL = (
    "https://earthquake.usgs.gov/earthquakes/feed/v1.0/"
    "summary/all_day.geojson"
)


def get_usgs():

    try:

        return fetch_json(USGS_URL)["features"]

    except Exception as e:

        print("USGS 오류:", e)

        return []
NASA_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"


def get_eonet():

    try:

        return fetch_json(NASA_URL)["events"]

    except Exception as e:

        print("NASA 오류:", e)

        return []
