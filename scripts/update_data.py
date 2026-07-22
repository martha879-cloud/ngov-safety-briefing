import json
import os
import requests
from datetime import datetime

API_KEY = os.getenv("MOFA_API_KEY")

URL = f"https://apis.data.go.kr/1262000/TravelWarningService/getTravelWarningList?serviceKey={API_KEY}&numOfRows=200&pageNo=1&_type=json"

TARGET_COUNTRIES = {
"라오스": "asia",
"캄보디아": "asia",
"케냐": "africa",
"페루": "latin",
"요르단": "middle"
}

response = requests.get(URL)
print("Status code:", response.status_code)
print("Response text:", response.text[:500])

# JSON 응답이 아닐 경우 확인

if response.status_code != 200:
    raise Exception(f"API 요청 실패: {response.status_code}")

try:
    data = response.json()
except Exception:
    raise Exception(f"JSON 응답이 아닙니다. 응답 내용: {response.text[:500]}")

items = data["response"]["body"]["items"]["item"]

countries = []

for item in items:
    name = item.get("countryName")

if name in TARGET_COUNTRIES:
    level = item.get("alarmLevel", "1")

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
        "issue": item.get("remark", "특이사항 없음"),
        "source": "MOFA",
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

with open("docs/data/countries.json", "w", encoding="utf-8") as f:
    json.dump(countries, f, ensure_ascii=False, indent=2)

print("MOFA data updated successfully!")
