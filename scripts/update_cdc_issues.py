"""
CDC Travel Health Notices(wwwnc.cdc.gov/travel/notices)를 파견국 20개국 기준으로 걸러서
docs/data/cdc_issues.json 으로 저장하는 스크립트.

CDC 페이지는 Level 1~4 섹션으로 나뉘어 있고, 각 알림(<li>)은
- 실제 상세페이지 링크: /travel/notices/level{N}/{slug}
- 날짜: <span class="date">
- 요약: <span class="summary"> (다국가 알림은 그 안에 "Destination List: ..."가 포함됨)
로 구성되어 있다.

WHO 때와 마찬가지로, CDC 목록에도 오래된(수년 전) 알림이 계속 남아있는 경우가 있어
RECENCY_DAYS 이내 것만 사용한다.
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from config import COUNTRIES


NOTICES_URL = "https://wwwnc.cdc.gov/travel/notices"
OUTPUT_FILE = Path("docs/data/cdc_issues.json")

RECENCY_DAYS = 180

LEVEL_TO_NUM = {"level1": 1, "level2": 2, "level3": 3, "level4": 4}

SEVERITY_BY_LEVEL = {1: "low", 2: "medium", 3: "high", 4: "critical"}

LEVEL_LABELS = {
    1: "Level 1 (Practice Usual Precautions)",
    2: "Level 2 (Practice Enhanced Precautions)",
    3: "Level 3 (Reconsider Nonessential Travel)",
    4: "Level 4 (Avoid All Travel)",
}


def fetch_notices_page():
    response = requests.get(NOTICES_URL, timeout=30, headers={
        "User-Agent": "KOICA-NGO-Safety-Dashboard"
    })
    response.raise_for_status()
    return response.text


def parse_notices(html):
    """레벨별 섹션에서 알림 목록을 뽑아낸다."""

    soup = BeautifulSoup(html, "html.parser")
    items = []

    for level_div in soup.find_all("div", id=re.compile(r"^level\d$")):

        level_num = LEVEL_TO_NUM.get(level_div.get("id"))

        if not level_num:
            continue

        for li in level_div.select("ul.list-block > li"):

            # 실제 상세 링크는 href가 /travel/notices/level 로 시작하는 a 태그
            detail_link = None

            for a in li.find_all("a"):
                href = a.get("href", "")
                if href.startswith("/travel/notices/level"):
                    detail_link = a
                    break

            if not detail_link:
                continue

            title = detail_link.get_text(strip=True)
            url = "https://wwwnc.cdc.gov" + detail_link["href"]

            date_span = li.find("span", class_="date")
            date_text = date_span.get_text(strip=True) if date_span else ""

            summary_span = li.find("span", class_="summary")
            summary_text = summary_span.get_text(" ", strip=True) if summary_span else ""

            dest_match = re.search(r"Destination List:\s*(.+)", summary_text)
            destinations = dest_match.group(1) if dest_match else ""

            # "Destination List: ..." 부분은 별도 목적지 목록이므로,
            # 요약 본문에서는 제거해서 보여준다.
            clean_summary = summary_text
            if dest_match:
                clean_summary = summary_text[:dest_match.start()].strip()

            items.append({
                "level": level_num,
                "title": title,
                "url": url,
                "date_text": date_text,
                "summary": clean_summary,
                "destinations": destinations,
            })

    return items


def parse_date(date_text):
    """'July 15, 2026' -> '2026-07-15'"""

    try:
        return datetime.strptime(date_text, "%B %d, %Y").strftime("%Y-%m-%d")
    except Exception:
        return None


def match_countries(item, countries):
    """제목 또는 목적지 목록에서 우리 파견국 영문명을 찾아 매칭되는 국가들을 반환."""

    search_text = f"{item['title']} {item['destinations']}"
    matched = []

    for country in countries:
        pattern = r"\b" + re.escape(country["name_en"]) + r"\b"
        if re.search(pattern, search_text):
            matched.append(country)

    return matched


def get_volunteer_impact(severity):

    if severity == "critical":
        return "CDC가 여행금지(Level 4)로 지정한 상황입니다. 활동 지속 여부를 즉시 재검토해야 합니다."

    if severity == "high":
        return "CDC가 비필수 여행 재고(Level 3)를 권고하는 상황입니다. 활동 지역의 안전 여부를 확인하세요."

    if severity == "medium":
        return "CDC가 강화된 예방조치(Level 2)를 권고하는 상황입니다. 예방접종 및 위생수칙을 확인하세요."

    return "CDC 기준으로는 낮은 위험도이나, 예방수칙을 참고하세요."


def get_recommended_action():
    return "CDC 여행건강경보 원문을 참고하여 필요한 예방접종·위생수칙을 점검하세요."


def build_issues():

    try:
        html = fetch_notices_page()
        raw_items = parse_notices(html)
    except Exception as e:
        print("CDC 여행건강경보 접속/파싱 실패:", e)
        return []

    print(f"CDC 알림 전체 수: {len(raw_items)}")

    cutoff = (datetime.now() - timedelta(days=RECENCY_DAYS)).strftime("%Y-%m-%d")

    issues = []

    for item in raw_items:

        published_at = parse_date(item["date_text"])

        if not published_at or published_at < cutoff:
            continue

        matched_countries = match_countries(item, COUNTRIES)

        for country in matched_countries:

            severity = SEVERITY_BY_LEVEL[item["level"]]

            issues.append({
                "id": f"cdc-{country['id']}-{published_at}-{item['level']}",
                "country": country["name"],
                "category": "health",
                "severity": severity,
                "title": f"{item['title']} ({LEVEL_LABELS[item['level']]})",
                "summary": item["summary"] or item["title"],
                "volunteer_impact": get_volunteer_impact(severity),
                "recommended_action": get_recommended_action(),
                "published_at": published_at,
                "source": "CDC",
                "source_url": item["url"],
            })

    return issues


def main():

    print("CDC 여행건강경보 수집 시작")

    issues = build_issues()

    issues.sort(key=lambda item: item["published_at"], reverse=True)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "issues": issues,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("파견국 관련 CDC 알림:", len(issues))
    print("저장 파일:", OUTPUT_FILE)
    print("CDC 여행건강경보 업데이트 완료")


if __name__ == "__main__":
    main()
