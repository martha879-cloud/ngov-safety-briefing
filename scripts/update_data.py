import json
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

API_KEY = os.getenv("MOFA_API_KEY")

URL = "https://apis.data.go.kr/1262000/TravelAlarmService2/getTravelAlarmList2"

params = {
"serviceKey": API_KEY,
"returnType": "JSON",
"numOfRows": 200,
"pageNo": 1
}

response = requests.get(URL, params=params)

print("Status code:", response.status_code)
print("Response text:", response.text[:500])

if response.status_code != 200:
    raise Exception(f"API 요청 실패: {response.status_code}")

data = response.json()
items = data["response"]["body"]["items"]["item"]


countries = []

for item in items:
    name = item.get("country_nm")

if name in TARGET_COUNTRIES:
    level = item.get("alarm_lvl", "1")

    status = "green"
    if level == "2":
        status = "yellow"
    elif level == "3":
        status = "orange"
    elif level == "4":
        status = "red"

    countries.append({
        "id": name.lower(),
        "name": name,
        "flag": "🌍",
        "region": TARGET_COUNTRIES[name],
        "status": status,
        "issue": item.get("alarm_msg", "특이사항 없음"),
        "source": "MOFA",
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

with open("docs/data/countries.json", "w", encoding="utf-8") as f:
    json.dump(countries, f, ensure_ascii=False, indent=2)

print("MOFA data updated successfully!")
