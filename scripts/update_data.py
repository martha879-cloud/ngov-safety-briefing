import json
import os
import requests
from datetime import datetime

API_KEY = os.getenv("MOFA_API_KEY")

URL = "https://apis.data.go.kr/1262000/TravelAlarmService2/getTravelAlarmList2"

TARGET_COUNTRIES = {
"동티모르": "asia",
"라오스": "asia",
"몽골": "asia",
"방글라데시": "asia",
"베트남": "asia",
"인도네시아": "asia",
"캄보디아": "asia",
"필리핀": "asia",
"르완다": "africa",
"말라위": "africa",
"모로코": "africa",
"우간다": "africa",
"이집트": "africa",
"케냐": "africa",
"탄자니아": "africa",
"과테말라": "latin",
"도미니카공화국": "latin",
"페루": "latin",
"요르단": "middle",
"키르기스스탄": "middle"
}

countries = []

for page in range(1, 21):
    print("Checking page:", page)

    params = {
        "serviceKey": API_KEY,
        "returnType": "JSON",
        "numOfRows": 100,
        "pageNo": page
    }

    response = requests.get(URL, params=params)

    if response.status_code != 200:
        continue

    data = response.json()

    items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])

    # item이 하나일 경우 dict로 오기 때문에 리스트로 변환
    if isinstance(items, dict):
        items = [items]

    print(f"Page {page} items:", len(items))

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
                
        # TARGET_COUNTRIES에 있는 국가만 저장하고 중복 제거 
        if name in TARGET_COUNTRIES and not any(c["name"] == name for c in countries):
            countries.append({
                "id": name.lower().replace(" ", "-"),
                "name": name,
                "flag": "🌍",
                "region": TARGET_COUNTRIES[name],
                "status": status,
                "issue": item.get("alarm_msg", "특이사항 없음"),
                "source": "MOFA",
                "updated": datetime.now().strftime("%Y-%m-%d %H:%M")
        })

print("Saved countries:", len(countries))

with open("docs/data/countries.json", "w", encoding="utf-8") as f:
    json.dump(countries, f, ensure_ascii=False, indent=2)

print("Saved countries:", len(countries))
print("MOFA data updated successfully!")
