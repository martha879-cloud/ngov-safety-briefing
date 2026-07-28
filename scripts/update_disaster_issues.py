"""
USGS 지진 데이터를 파견국 20개국 기준으로 걸러서
docs/data/disaster_issues.json 으로 저장하는 스크립트.

safety_issues.json / news_issues.json과 동일한 방식으로,
매 실행마다 "최근 지진 목록"을 새로 통째로 만든다 (누적/중복제거 상태를 따로 들고 있지 않음).
USGS 피드 자체가 최근 1주일(4.5+) 창을 계속 돌려주기 때문에,
지진이 알아서 창 밖으로 밀려나면서 자연스럽게 최신 상태로 유지된다.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

from config import COUNTRIES
from sources import get_usgs


OUTPUT_FILE = Path("docs/data/disaster_issues.json")

# 지진 결과에서 국가를 매칭할 때 쓰는 영문 국명.
# USGS place 문자열은 보통 "10km SW of Lima, Peru"처럼 끝에 국가/지역명이 붙는다.
COUNTRY_ALIASES = {c["id"]: [c["name_en"]] for c in COUNTRIES}
COUNTRY_ALIASES["timor-leste"].append("East Timor")
COUNTRY_ID_TO_INFO = {c["id"]: c for c in COUNTRIES}


def match_country(place):
    """USGS place 문자열에서 우리 파견국 중 하나를 찾아 country id를 반환.
    못 찾으면 None."""

    if not place:
        return None

    for country_id, aliases in COUNTRY_ALIASES.items():
        for alias in aliases:
            if alias.lower() in place.lower():
                return country_id

    return None


def classify_severity(magnitude):

    if magnitude is None:
        return "low"

    if magnitude >= 7.0:
        return "critical"

    if magnitude >= 6.0:
        return "high"

    if magnitude >= 5.0:
        return "medium"

    return "low"


def get_volunteer_impact(severity):

    if severity == "critical":
        return "대규모 인명·재산 피해 가능성이 있어 즉시 안전 확인이 필요합니다."

    if severity == "high":
        return "여진 및 추가 피해 가능성이 있어 활동 지역 안전 확인이 필요합니다."

    if severity == "medium":
        return "체감 진동이 있을 수 있어 현지 상황을 확인하는 것이 좋습니다."

    return "경미한 규모이나 현지 소식을 계속 확인하세요."


def get_recommended_action(severity):

    if severity in ("critical", "high"):
        return "현지 협력기관 및 담당자와 즉시 상황을 공유하고 안전 여부를 확인하세요."

    return "USGS 및 현지 뉴스를 통해 여진 여부와 피해 상황을 계속 확인하세요."


def build_issue(feature, country_id):

    props = feature.get("properties", {})
    geometry = feature.get("geometry", {})
    coords = geometry.get("coordinates", [None, None, None])

    magnitude = props.get("mag")
    place = props.get("place", "")
    event_time_ms = props.get("time")
    source_url = props.get("url", "")

    if event_time_ms:
        published_at = (
            datetime.fromtimestamp(event_time_ms / 1000, tz=timezone.utc)
            .strftime("%Y-%m-%d")
        )
    else:
        published_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    severity = classify_severity(magnitude)
    country_info = COUNTRY_ID_TO_INFO[country_id]

    mag_text = (
        f"M{magnitude:.1f}"
        if isinstance(magnitude, (int, float))
        else "규모 미상"
    )

    return {
        "id": f"usgs-{feature.get('id')}",
        "country": country_info["name"],
        "category": "natural_disaster",
        "severity": severity,
        "title": f"{mag_text} 지진 발생 ({place or country_info['name']})",
        "summary": f"USGS 관측 기준 {mag_text} 규모의 지진이 발생했습니다 ({place}).",
        "volunteer_impact": get_volunteer_impact(severity),
        "recommended_action": get_recommended_action(severity),
        "published_at": published_at,
        "source": "USGS",
        "source_url": source_url,
        "lat": coords[1],
        "lng": coords[0],
        "magnitude": magnitude,
    }


def main():

    print("USGS 지진 데이터 수집 시작")

    features = get_usgs()

    print(f"USGS 전체 지진 수: {len(features)}")

    issues = []
    seen_feature_ids = set()

    for feature in features:

        feature_id = feature.get("id")

        if feature_id in seen_feature_ids:
            continue

        place = feature.get("properties", {}).get("place", "")

        country_id = match_country(place)

        if not country_id:
            continue

        issues.append(build_issue(feature, country_id))
        seen_feature_ids.add(feature_id)

    issues.sort(key=lambda item: item["published_at"], reverse=True)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "issues": issues,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("파견국 관련 지진:", len(issues))
    print("저장 파일:", OUTPUT_FILE)
    print("USGS 지진 데이터 업데이트 완료")


if __name__ == "__main__":
    main()
