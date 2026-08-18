"""
미국 국무부(Travel.State.Gov) 여행경보 RSS를 파견국 20개국 기준으로 걸러서
docs/data/state_dept_issues.json 으로 저장하는 스크립트.

이 RSS는 "전체 213개국 목록"이 아니라 "최근에 갱신된 국가들"만 보여주는
피드이기 때문에, 우리 20개국 중 최근에 갱신이 없었던 국가는 자연스럽게
이번 실행 결과에 나타나지 않는다 (safety_issues/news_issues와 동일한 성격).
"""

import json
import html
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests
import xml.etree.ElementTree as ET

from config import COUNTRIES
from time_util import kst_now
from translate_util import translate_to_korean


RSS_URL = "https://travel.state.gov/_res/rss/TAsTWs.xml"
OUTPUT_FILE = Path("docs/data/state_dept_issues.json")

# 국가명 매칭용 (제목이 "국가명 - Level N: ..." 형태로 오기 때문에 영문명 그대로 사용)
COUNTRY_BY_NAME_EN = {c["name_en"]: c for c in COUNTRIES}

LEVEL_SEVERITY = {
    "1": "low",
    "2": "medium",
    "3": "high",
    "4": "critical",
}


def strip_html(text):
    """설명(description)의 HTML 태그와 엔티티(&nbsp; 등)를 제거하고 짧게 자름"""

    if not text:
        return ""

    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()

    return text[:300]


def match_country(title):
    """제목 앞부분에서 우리 파견국 영문명을 찾아 country dict 반환.
    못 찾으면 None."""

    for name_en, country in COUNTRY_BY_NAME_EN.items():
        if title.startswith(name_en + " - Level"):
            return country

    return None


def parse_level(category_text):
    """'Level 2: Exercise Increased Caution' -> '2'"""

    match = re.search(r"Level\s+(\d)", category_text or "")

    return match.group(1) if match else None


def parse_pub_date(pub_date_text):
    """RSS pubDate를 YYYY-MM-DD로 변환. 파싱 실패 시 오늘 날짜.
    이 피드는 'Thu, 04 Jun 2026'처럼 시간 없이 날짜만 오는 경우가 있어
    표준 RFC822 파서(parsedate_to_datetime)가 실패할 수 있으므로 직접 파싱도 시도한다."""

    if not pub_date_text:
        return kst_now().strftime("%Y-%m-%d")

    try:
        return parsedate_to_datetime(pub_date_text).strftime("%Y-%m-%d")
    except Exception:
        pass

    try:
        return datetime.strptime(pub_date_text.strip(), "%a, %d %b %Y").strftime("%Y-%m-%d")
    except Exception:
        pass

    return kst_now().strftime("%Y-%m-%d")


def classify_category(text):

    text = text.lower()

    if any(w in text for w in ["earthquake", "flood", "storm", "hurricane", "volcano", "tsunami", "natural disaster"]):
        return "natural_disaster"

    if any(w in text for w in ["ebola", "outbreak", "epidemic", "disease", "health"]):
        return "health"

    if any(w in text for w in ["armed conflict", "war", "terrorism", "attack", "unrest", "protest"]):
        return "conflict"

    if any(w in text for w in ["crime", "kidnapping", "robbery"]):
        return "security"

    if any(w in text for w in ["airport", "flight", "transport"]):
        return "transport"

    return "official_notice"


def get_volunteer_impact(severity):

    if severity == "critical":
        return "미국 국무부가 여행금지(4단계)로 지정한 국가입니다. 활동 지속 여부를 즉시 재검토해야 합니다."

    if severity == "high":
        return "미국 국무부가 철수권고(3단계)로 지정한 국가입니다. 활동 지역의 안전 여부를 확인하세요."

    if severity == "medium":
        return "미국 국무부가 여행자제(2단계)로 지정한 국가입니다. 세부 위험 지역을 확인하는 것이 좋습니다."

    return "미국 국무부 기준으로는 낮은 위험도이나, 세부 내용을 참고하세요."


def get_recommended_action(severity):

    if severity in ("critical", "high"):
        return "현지 협력기관 및 담당자와 상황을 공유하고, 미국 국무부 권고 사항을 함께 검토하세요."

    return "미국 국무부 여행경보 원문을 참고하여 세부 위험 지역 및 주의사항을 확인하세요."


def fetch_advisories():

    response = requests.get(RSS_URL, timeout=30, headers={
        "User-Agent": "KOICA-NGO-Safety-Dashboard"
    })
    response.raise_for_status()

    root = ET.fromstring(response.content)

    return root.findall(".//item")


def build_issues():

    try:
        items = fetch_advisories()
    except Exception as e:
        print("미국 국무부 RSS 접속 실패:", e)
        return []

    print(f"RSS 전체 항목 수: {len(items)}")

    issues = []

    for item in items:

        title = (item.findtext("title") or "").strip()

        country = match_country(title)

        if not country:
            continue

        link = (item.findtext("link") or "").strip()
        pub_date = item.findtext("pubDate")
        description = item.findtext("description") or ""

        threat_level_el = item.find("./category[@domain='Threat-Level']")
        threat_level_text = threat_level_el.text if threat_level_el is not None else ""

        level = parse_level(threat_level_text)
        severity = LEVEL_SEVERITY.get(level, "low")

        summary_en = strip_html(description)
        summary = translate_to_korean(summary_en) if summary_en else ""
        category = classify_category(f"{title} {summary_en}")

        issues.append({
            "id": f"statedept-{country['id']}-{parse_pub_date(pub_date)}",
            "country": country["name"],
            "category": category,
            "severity": severity,
            "title": title,
            "summary": summary or "미국 국무부 여행경보 갱신 내역입니다.",
            "summary_en": summary_en,
            "volunteer_impact": get_volunteer_impact(severity),
            "recommended_action": get_recommended_action(severity),
            "published_at": parse_pub_date(pub_date),
            "source": "US State Dept",
            "source_url": link,
        })

    return issues


def main():

    print("미국 국무부 여행경보 수집 시작")

    issues = build_issues()

    issues.sort(key=lambda item: item["published_at"], reverse=True)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "updated": kst_now().strftime("%Y-%m-%d %H:%M"),
        "issues": issues,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("파견국 관련 항목:", len(issues))
    print("저장 파일:", OUTPUT_FILE)
    print("미국 국무부 여행경보 업데이트 완료")


if __name__ == "__main__":
    main()
