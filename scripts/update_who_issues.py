"""
WHO 발병정보(Disease Outbreak News, DON)를 파견국 20개국 기준으로 걸러서
docs/data/who_issues.json 으로 저장하는 스크립트.

WHO는 이 목록에 대한 깔끔한 공식 API를 제공하지 않아서, 페이지를 직접 파싱한다.
페이지 구조가 바뀌면 이 스크래핑도 깨질 수 있으므로, 접속/파싱 실패 시
예외를 발생시키지 않고 조용히 빈 목록을 저장한다 (기존 파일을 덮어쓰지 않으려면
워크플로우에서 실패를 감지해 커밋을 건너뛰는 방식도 고려 가능).
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from config import COUNTRIES


DON_LIST_URL = "https://www.who.int/emergencies/emergency-events/item"
OUTPUT_FILE = Path("docs/data/who_issues.json")

# WHO DON 페이지가 수십 년치 아카이브를 한 번에 보여주기 때문에,
# 최근 이 기간(일) 이내의 발표만 "현재 유효한 이슈"로 간주한다.
RECENCY_DAYS = 180

# 국가명 매칭용 (DON 제목이 보통 "질병명 - 국가명" 형태로 끝남)
COUNTRY_BY_NAME_EN = {c["name_en"]: c for c in COUNTRIES}

# DON 항목 하나의 텍스트에서 "제목"과 "날짜"를 뽑아내는 패턴.
# 실제 페이지 텍스트 예: "Disease Outbreak News Nipah virus infection - Bangladesh 6 February 2026 | ..."
ITEM_PATTERN = re.compile(
    r"Disease Outbreak News\s*(.+?)\s*(\d{1,2}\s+\w+\s+\d{4})\s*\|",
    re.IGNORECASE,
)

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}


def match_country(title):
    """제목에 우리 파견국 영문명이 포함되어 있는지 확인.
    'Global', 'Multi-country', 'Region' 등 특정 국가가 아닌 경우는 자동으로 매칭 안 됨."""

    for name_en, country in COUNTRY_BY_NAME_EN.items():
        if name_en in title:
            return country

    return None


def parse_date(date_text):
    """'6 February 2026' -> '2026-02-06'"""

    match = re.match(r"(\d{1,2})\s+(\w+)\s+(\d{4})", date_text)

    if not match:
        return datetime.now().strftime("%Y-%m-%d")

    day, month_name, year = match.groups()
    month = MONTHS.get(month_name.lower())

    if not month:
        return datetime.now().strftime("%Y-%m-%d")

    try:
        return datetime(int(year), month, int(day)).strftime("%Y-%m-%d")
    except ValueError:
        return datetime.now().strftime("%Y-%m-%d")


def get_volunteer_impact(title):
    return f"WHO가 발표한 발병 정보입니다 ({title}). 관련 예방수칙 및 건강관리 여부를 확인하세요."


def get_recommended_action():
    return "WHO 발병정보 원문과 현지 보건당국 발표를 확인하고, 필요한 예방접종·위생수칙을 점검하세요."


def fetch_don_items():

    response = requests.get(DON_LIST_URL, timeout=30, headers={
        "User-Agent": "KOICA-NGO-Safety-Dashboard"
    })
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # href에 'disease-outbreak-news/item'이 들어간 링크만 선택.
    # (WHO 사이트 CSS 클래스는 언제든 바뀔 수 있어, URL 패턴 기반으로 최대한 안정적으로 선택)
    links = soup.find_all("a", href=re.compile(r"disease-outbreak-news/item"))

    items = []

    for link in links:

        text = link.get_text(" ", strip=True)
        href = link.get("href", "")

        match = ITEM_PATTERN.search(text)

        if not match:
            continue

        title = match.group(1).strip(" -–|")
        date_text = match.group(2).strip()

        if href.startswith("http"):
            url = href
        else:
            url = "https://www.who.int" + href

        items.append({
            "title": title,
            "date_text": date_text,
            "url": url,
        })

    return items


def build_issues():

    try:
        raw_items = fetch_don_items()
    except Exception as e:
        print("WHO 발병정보 접속/파싱 실패:", e)
        return []

    print(f"WHO DON 전체 항목 수: {len(raw_items)}")

    # WHO DON 페이지는 수십 년치 과거 기록을 통째로 보여주기 때문에,
    # 최근 것만 남기지 않으면 1990년대 기록까지 다 섞여 나온다.
    cutoff = (datetime.now() - timedelta(days=RECENCY_DAYS)).strftime("%Y-%m-%d")

    # (국가, 제목)이 같으면 같은 발병 상황의 반복 업데이트이므로,
    # 가장 최근 날짜의 것 하나만 남긴다.
    latest_by_key = {}

    for item in raw_items:

        country = match_country(item["title"])

        if not country:
            continue

        published_at = parse_date(item["date_text"])

        if published_at < cutoff:
            continue

        dedup_key = (country["id"], item["title"])

        existing = latest_by_key.get(dedup_key)

        if existing and existing["published_at"] >= published_at:
            continue

        latest_by_key[dedup_key] = {
            "country": country,
            "title": item["title"],
            "published_at": published_at,
            "url": item["url"],
        }

    issues = []

    for entry in latest_by_key.values():

        country = entry["country"]
        title = entry["title"]
        published_at = entry["published_at"]

        issues.append({
            "id": f"who-{country['id']}-{published_at}",
            "country": country["name"],
            "category": "health",
            "severity": "medium",
            "title": title,
            "summary": f"WHO Disease Outbreak News: {title}",
            "volunteer_impact": get_volunteer_impact(title),
            "recommended_action": get_recommended_action(),
            "published_at": published_at,
            "source": "WHO",
            "source_url": entry["url"],
        })

    return issues


def main():

    print("WHO 발병정보 수집 시작")

    issues = build_issues()

    issues.sort(key=lambda item: item["published_at"], reverse=True)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "issues": issues,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("파견국 관련 발병정보:", len(issues))
    print("저장 파일:", OUTPUT_FILE)
    print("WHO 발병정보 업데이트 완료")


if __name__ == "__main__":
    main()
