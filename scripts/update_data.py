import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "docs" / "data"

COUNTRIES = [
    {
        "id": "kenya",
        "name": "케냐",
        "flag": "🇰🇪",
        "region": "africa"
    },
    {
        "id": "peru",
        "name": "페루",
        "flag": "🇵🇪",
        "region": "latin"
    },
    {
        "id": "bangladesh",
        "name": "방글라데시",
        "flag": "🇧🇩",
        "region": "asia"
    }
]

countries = []

for c in COUNTRIES:

    countries.append({
        "id": c["id"],
        "name": c["name"],
        "flag": c["flag"],
        "region": c["region"],
        "status": "green",
        "priority": 1,
        "issue": "특이사항 없음",
        "source": "",
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M")
    })

with open(DATA_DIR / "countries.json", "w", encoding="utf-8") as f:
    json.dump(countries, f, ensure_ascii=False, indent=2)

with open(DATA_DIR / "last_update.json", "w", encoding="utf-8") as f:
    json.dump(
        {
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M")
        },
        f,
        ensure_ascii=False,
        indent=2
    )

print("✅ countries.json 생성 완료")
