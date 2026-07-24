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
        "lat": country.get("lat"),
        "lng": country.get("lng"),
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


def is_partial_region(region_ty):
    """region_ty가 '국가 일부 지역'만 해당하는 경보인지 여부.
    (예: 필리핀 잠보앙가/술루/바실란/타위타위처럼 국가 전체가 아닌
    특정 분쟁지역 한정 경보가 국가 전체 상태로 오인되는 것을 방지)"""
    return bool(region_ty) and "일부" in region_ty


def choose_representative(items):
    """한 국가에 지역별로 여러 경보 레코드가 있을 때 대표 레코드를 선택.
    국가 전체를 가리키는 레코드를 최우선으로 쓰고, 그런 레코드가 없을 때만
    일부 지역 레코드 중 가장 낮은(안전한) 단계를 대신 사용한다."""

    whole = [i for i in items if not is_partial_region(i.get("region_ty"))]
    pool = whole if whole else items

    chosen = min(pool, key=lambda i: int(i.get("alarm_lvl") or 1))
    is_partial_only = not whole

    return chosen, is_partial_only


def fetch_mofa_alerts():
    """외교부 여행경보 API에서 대상 국가에 해당하는 항목을 모두 모아서 반환.
    한 국가에 지역별로 여러 레코드가 있을 수 있으므로, 국가별로 리스트에 모은 뒤
    choose_representative()로 대표 레코드를 고른다."""

    raw_by_country = {}

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

            raw_by_country.setdefault(name, []).append(item)

    matched = {}

    for name, items in raw_by_country.items():
        chosen, is_partial_only = choose_representative(items)

        level = chosen.get("alarm_lvl")
        issue = build_issue_text(level, chosen.get("written_dt"))

        if is_partial_only:
            issue += " (일부 지역 한정 경보이며, 지역별로 상이할 수 있음 · 0404.go.kr 확인 권장)"

        matched[name] = {
            "status": level_to_status(level),
            "issue": issue,
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
