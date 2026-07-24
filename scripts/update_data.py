import json
import os
import requests
from datetime import datetime

from config import COUNTRIES

API_KEY = os.getenv("MOFA_API_KEY")

URL = "https://apis.data.go.kr/1262000/TravelAlarmService2/getTravelAlarmList2"

# 외교부 API 국가명과 우리 목록명이 다른 경우 매핑
NAME_MAPPING = {
    "티모르레스테": "동티모르",
    "도미니카 공화국": "도미니카공화국",
    "키르기즈공화국": "키르기스스탄",
}

# 국가명 -> country dict (config/countries.json 기준)
COUNTRY_BY_NAME = {c["name"]: c for c in COUNTRIES}


def default_entry(country):
    """API에서 못 찾은 국가도 이 기본값으로 항상 표시됩니다."""
    return {
        "id": country["id"],
        "name": country["name"],
        "flag": country["flag"],
        "region": country["region"],
        "status": "green",
        "issue": "특이사항 없음",
        "source": "",
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


def level_to_status(level):
    return {"2": "yellow", "3": "orange", "4": "red"}.get(level, "green")


# 외교부 여행경보 4단계 공식 명칭 (alarm_lvl 값 기준)
LEVEL_LABELS = {
    "1": "여행유의(남색경보)",
    "2": "여행자제(황색경보)",
    "3": "철수권고(적색경보)",
    "4": "여행금지(흑색경보)",
}


def build_issue_text(level, written_dt):
    """실제 API가 주는 필드(alarm_lvl, written_dt)만으로 상황 텍스트를 구성.
    alarm_msg 필드는 이 API에 존재하지 않으므로 사용하지 않음."""

    label = LEVEL_LABELS.get(level)

    if not label:
        return "특이사항 없음"

    if written_dt:
        return f"외교부 여행경보: {label} (발령일 {written_dt})"

    return f"외교부 여행경보: {label}"


def fetch_mofa_alerts():
    """외교부 여행경보 API에서 대상 국가에 해당하는 항목만 모아서 반환"""
    matched = {}

    for page in range(1, 21):
        print("Checking page:", page)

        params = {
            "serviceKey": API_KEY,
            "returnType": "JSON",
            "numOfRows": 100,
            "pageNo": page,
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
            name = NAME_MAPPING.get(name, name)

            if name not in COUNTRY_BY_NAME:
                continue

            # 같은 국가가 여러 항목으로 올 경우 첫 매칭만 사용
            if name in matched:
                continue

            matched[name] = {
                "status": level_to_status(item.get("alarm_lvl", "1")),
                "issue": build_issue_text(item.get("alarm_lvl"), item.get("written_dt")),
                "source": "MOFA",
                "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }

    return matched


def build_countries():
    """config/countries.json에 있는 20개국을 항상 전부 포함해서 반환.
    API에서 매칭되지 않은 국가는 기본값(green/특이사항 없음)을 사용합니다."""

    alerts = fetch_mofa_alerts()

    result = []
    for country in COUNTRIES:
        entry = default_entry(country)

        alert = alerts.get(country["name"])
        if alert:
            entry.update(alert)

        result.append(entry)

    return result


if __name__ == "__main__":
    countries = build_countries()

    print("Saved countries:", len(countries))

    with open("docs/data/countries.json", "w", encoding="utf-8") as f:
        json.dump(countries, f, ensure_ascii=False, indent=2)

    print("MOFA data updated successfully!")
