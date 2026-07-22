import json
from datetime import datetime

# 현재는 테스트용 자동수집 예시입니다.

# 나중에 외교부 API로 실제 데이터를 가져오도록 확장합니다.

countries = [
{
"id": "laos",
"name": "라오스",
"flag": "🇱🇦",
"region": "asia",
"status": "green",
"issue": "특이사항 없음",
"source": "MOFA",
"updated": datetime.now().strftime("%Y-%m-%d %H:%M")
},
{
"id": "cambodia",
"name": "캄보디아",
"flag": "🇰🇭",
"region": "asia",
"status": "yellow",
"issue": "우기 홍수 모니터링",
"source": "ReliefWeb",
"updated": datetime.now().strftime("%Y-%m-%d %H:%M")
}
]

with open("docs/data/countries.json", "w", encoding="utf-8") as f:
json.dump(countries, f, ensure_ascii=False, indent=2)

print("countries.json updated successfully!")
