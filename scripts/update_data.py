from datetime import datetime
import json

today = datetime.now().strftime("%Y-%m-%d %H:%M")

countries = [
    {
        "id":"timor-leste",
        "status":"green"
    },
    {
        "id":"laos",
        "status":"green"
    },
    {
        "id":"mongolia",
        "status":"green"
    }
]

with open("docs/data/last_update.json","w",encoding="utf-8") as f:

    json.dump(
        {
            "updated":today
        },
        f,
        ensure_ascii=False,
        indent=4
    )

print("Update Complete")
