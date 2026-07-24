# scripts/rules.py

STATUS = {
    "green": {
        "priority": 1,
        "label": "활동 가능"
    },
    "yellow": {
        "priority": 2,
        "label": "모니터링"
    },
    "orange": {
        "priority": 3,
        "label": "조치 검토"
    },
    "red": {
        "priority": 4,
        "label": "긴급 대응"
    }
}
def default_status(country):

    return {
        "id": country["id"],
        "name": country["name"],
        "flag": country.get("flag", ""),
        "region": country["region"],

        "status": "green",
        "priority": 1,

        "issue": "특이사항 없음",

        "source": "",

        "reason": "",

        "updated": "",

        "links": []
    }
def update_status(country, status, issue, source, updated, reason=""):

    if STATUS[status]["priority"] > country["priority"]:

        country["status"] = status
        country["priority"] = STATUS[status]["priority"]

        country["issue"] = issue
        country["source"] = source
        country["updated"] = updated
        country["reason"] = reason

    return country
