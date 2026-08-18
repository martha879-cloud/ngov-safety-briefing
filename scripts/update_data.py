import json
import os
import requests
from datetime import datetime
from pathlib import Path

from config import COUNTRIES
from time_util import kst_now_str

API_KEY = os.getenv("MOFA_API_KEY")

URL = "https://apis.data.go.kr/1262000/TravelAlarmService2/getTravelAlarmList2"

# 0404.go.kr 국가/지역별 정보 목록 스크래핑 결과 (scrape_mofa_country_list.py가 생성).
# TravelAlarmService2 API가 놓치는 국가(우간다, 키르기스스탄 등)를 보완하고,
# 특별여행주의보 여부를 알려주는 데 사용한다.
SUPPLEMENT_FILE = Path("data/processed/mofa_country_levels.json")

# 0404.go.kr '여행경보 조정' 게시판 스크래핑 결과 (scrape_travel_alert_reasons.py가 생성).
# TravelAlarmService2 API는 조정 사유 텍스트를 안 주기 때문에, 여기서 보완한다.
REASON_FILE = Path("data/processed/travel_alert_reasons.json")

# 외교부 API 국가명과 우리 목록명이 다른 경우 매핑
NAME_MAPPING = {
    "티모르레스테": "동티모르",
    "도미니카 공화국": "도미니카공화국",
    "키르기즈공화국": "키르기스스탄",
}

# 국가명 -> country dict (config/countries.json 기준)
COUNTRY_BY_NAME = {c["name"]: c for c in COUNTRIES}


def load_supplement():
    """0404.go.kr 국가 목록 스크래핑 결과를 불러온다. 없으면 빈 dict."""

    if not SUPPLEMENT_FILE.exists():
        return {}

    with open(SUPPLEMENT_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_reasons():
    """여행경보 조정 사유 스크래핑 결과를 불러온다. 없으면 빈 dict."""

    if not REASON_FILE.exists():
        return {}

    with open(REASON_FILE, encoding="utf-8") as f:
        return json.load(f)


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
        "issue": "여행경보 미지정",
        "source": "",
        "updated": kst_now_str(),
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
        return "여행경보 미지정"

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
    all_country_names_seen = set()

    for page in range(1, 21):
        print("Checking page:", page)

        params = {
            "serviceKey": API_KEY,
            "returnType": "JSON",
            "numOfRows": 100,
            "pageNo": page,
        }

        try:
            response = requests.get(URL, params=params, timeout=30)
        except requests.RequestException as e:
            # 이 API가 가끔 타임아웃/접속 실패를 일으키는 걸 실제로 겪었다.
            # 여기서 예외를 그냥 던지면 스크립트 전체가 죽어서(exit code 1),
            # 이 실행에서는 국가 데이터가 아예 갱신이 안 되는 상황이 생긴다.
            # 지금까지 모은 페이지만이라도 쓰도록 반복을 멈추고 넘어간다.
            print(f"페이지 {page} 요청 실패, 지금까지 모은 데이터로 진행:", e)
            break

        if response.status_code != 200:
            continue

        data = response.json()
        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])

        # item이 하나일 경우 dict로 오기 때문에 리스트로 변환
        if isinstance(items, dict):
            items = [items]

        print(f"Page {page} items:", len(items))

        if not items:
            # 응답이 비어있으면 더 이상 페이지가 없다는 뜻이므로 중단
            break

        for item in items:
            raw_name = item.get("country_nm")
            all_country_names_seen.add(raw_name)

            name = NAME_MAPPING.get(raw_name, raw_name)

            if name not in COUNTRY_BY_NAME:
                continue

            raw_by_country.setdefault(name, []).append(item)

    # 진단용 로그: 우리 파견국 중 이번 실행에서 API 응답에 전혀 안 잡힌 국가가 있는지 확인.
    # (이름 표기가 달라서 놓친 건지, 아니면 API에 정말 해당 국가 레코드가 없는 건지 판단하는 데 사용)
    missing = [name for name in COUNTRY_BY_NAME if name not in raw_by_country]

    if missing:
        print("경고: 이번 실행에서 외교부 API 응답에 안 잡힌 파견국:", missing)
        print(f"참고: API가 실제로 반환한 국가명 전체 목록 ({len(all_country_names_seen)}개):")
        print(sorted(all_country_names_seen))

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
            "updated": kst_now_str(),
        }

    return matched


def apply_supplement(entry, country_name, supplement):
    """0404.go.kr 국가 목록 스크래핑 결과로 API 결과를 보완한다.

    1) API에서 아예 못 찾은 국가(entry["source"] == "")는 이 사이트의 단계로 대신 채운다.
    2) 특별여행주의보가 있으면(API 결과와 무관하게) 항상 이슈 텍스트에 표시한다."""

    info = supplement.get(country_name)

    if not info:
        return entry

    levels = info.get("levels") or []
    has_special = info.get("has_special", False)

    # 1) API가 못 찾은 국가를 이 사이트의 단계로 보완
    if entry["source"] == "" and levels:
        top_level = str(max(levels))

        entry["status"] = level_to_status(top_level)
        entry["issue"] = build_issue_text(top_level, None)
        entry["source"] = "MOFA(국가정보)"

    # 2) 특별여행주의보는 API에 필드 자체가 없으므로, 있으면 항상 별도로 덧붙인다
    if has_special:

        note = "⚠ 특별여행주의보 발령 중 (0404.go.kr 확인 필요)"

        if entry["source"] == "":
            # 일반 단계 없이 특별여행주의보만 있는 경우 (예: 우간다)
            entry["status"] = "orange"
            entry["issue"] = note
            entry["source"] = "MOFA(국가정보)"
        else:
            entry["issue"] = f"{entry['issue']} · {note}"

    return entry


def apply_reason(entry, country_name, reasons):
    """여행경보 조정 게시판에서 찾은 사유가 있으면 entry에 붙여준다.
    (외교부 API 자체는 사유 텍스트가 없어서, 있으면 항상 참고용으로 덧붙이는 것.
    현재 단계(level)와 이 사유가 같은 조정 건인지까지는 확인하지 않으므로,
    화면에는 "최근 조정 사유(날짜)"로 표시해 시점을 알 수 있게 한다.)"""

    info = reasons.get(country_name)

    if not info:
        return entry

    entry["adjustment_reason"] = info.get("reason", "")
    entry["adjustment_reason_date"] = info.get("published_at")
    entry["adjustment_reason_url"] = info.get("detail_url")

    return entry


def build_countries():
    """config/countries.json에 있는 20개국을 항상 전부 포함해서 반환.
    API에서 매칭되지 않은 국가는 기본값(green/여행경보 미지정)을 사용하고,
    0404.go.kr 스크래핑 결과로 한 번 더 보완합니다."""

    alerts = fetch_mofa_alerts()
    supplement = load_supplement()
    reasons = load_reasons()

    result = []
    for country in COUNTRIES:
        entry = default_entry(country)

        alert = alerts.get(country["name"])
        if alert:
            entry.update(alert)

        entry = apply_supplement(entry, country["name"], supplement)
        entry = apply_reason(entry, country["name"], reasons)

        result.append(entry)

    return result


if __name__ == "__main__":
    countries = build_countries()

    print("Saved countries:", len(countries))

    with open("docs/data/countries.json", "w", encoding="utf-8") as f:
        json.dump(countries, f, ensure_ascii=False, indent=2)

    print("MOFA data updated successfully!")
