"""
0404.go.kr '여행경보 조정' 게시판(/bbs/travelAlertAjmt/list)을 스크래핑해서
파견국 20개국의 최근 여행경보 조정 "사유" 전문을 뽑아낸다.

TravelAlarmService2 API(update_data.py가 쓰는 API)는 alarm_lvl/written_dt만 주고
"왜 조정됐는지"는 안 준다 (alarm_msg 필드 자체가 없음). 반면 이 게시판은
"세네갈 일부 지역 여행경보 상향 조정", "르완다, 아제르바이잔 여행경보단계 신규지정..." 처럼
실제 조정 배경을 설명하는 공지 전문을 올리기 때문에, 여기서 사유를 보완해온다.

결과는 data/processed/travel_alert_reasons.json 에 저장되고,
update_data.py가 이 파일을 읽어서 국가별 entry에 "adjustment_reason" 필드로 붙여준다.

이 게시판의 실제 상세페이지 HTML 마크업(클래스명 등)은 직접 확인하지 못한 상태로 작성했기
때문에, 셀렉터를 여러 개 순서대로 시도하고 전부 실패하면 제목만이라도 사유로 쓰도록
안전하게 설계했다. 나중에 실제 결과를 보고 셀렉터를 다듬어야 할 수 있다.
"""

import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from config import COUNTRIES

LIST_URL = "https://www.0404.go.kr/bbs/travelAlertAjmt/list"
BASE_URL = "https://www.0404.go.kr"

OUTPUT_FILE = Path("data/processed/travel_alert_reasons.json")

TARGET_COUNTRIES = [c["name"] for c in COUNTRIES]

MAX_REASON_LENGTH = 300

# 이 게시판은 페이지네이션이 있을 수 있어서, 최근 조정분을 놓치지 않도록
# 앞쪽 몇 페이지 정도만 확인한다 (매일 도는 스크립트라 이 정도면 충분).
MAX_PAGES = 3


def fetch_page(url, params=None):
    response = requests.get(url, params=params, timeout=30, headers={
        "User-Agent": "KOICA-NGO-Safety-Dashboard"
    })
    response.raise_for_status()
    return response.text


def clean_text(text):
    text = re.sub(r"\s+", " ", text).strip()
    return text[:MAX_REASON_LENGTH]


def extract_detail_text(html):
    """상세 페이지 본문에서 실제 조정 사유 문단을 최대한 뽑아낸다.
    사이트 마크업을 정확히 모르는 상태라, 흔히 쓰이는 본문 셀렉터를 순서대로 시도하고,
    전부 실패하면 <p> 태그들을 모아 쓴다. 그것도 없으면 빈 문자열(호출부에서 제목으로 대체)."""

    soup = BeautifulSoup(html, "html.parser")

    for selector in [
        ".view-content", ".board-view", ".bbs-view", ".cont-view",
        ".view-cont", "#content .view", "article",
    ]:
        el = soup.select_one(selector)
        if el:
            text = el.get_text("\n", strip=True)
            if len(text) > 30:
                return clean_text(text)

    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    paragraphs = [p for p in paragraphs if len(p) > 10]

    if paragraphs:
        return clean_text(" ".join(paragraphs))

    return ""


def parse_list(html):
    """목록 페이지에서 우리 파견국 이름이 제목에 들어간 행만 뽑아낸다."""

    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("tr")

    items = []

    for row in rows:

        row_text = row.get_text(" ", strip=True)

        if not row_text:
            continue

        matched = [name for name in TARGET_COUNTRIES if name in row_text]

        if not matched:
            continue

        link = row.find("a")

        if link is None:
            continue

        href = link.get("href", "")

        if href.startswith("http"):
            detail_url = href
        elif href.startswith("/"):
            detail_url = BASE_URL + href
        else:
            detail_url = BASE_URL + "/" + href.lstrip("/")

        title = link.get_text(" ", strip=True)

        if not title:
            continue

        date_match = re.search(r"\d{4}-\d{2}-\d{2}", row_text)
        published_at = date_match.group() if date_match else None

        items.append({
            "countries": matched,
            "title": title,
            "detail_url": detail_url,
            "published_at": published_at,
        })

    return items


def load_previous():
    """이전 실행 결과를 불러온다 (완전 실패 시 이걸 그대로 유지하기 위함)."""

    if not OUTPUT_FILE.exists():
        return {}

    try:
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def build_reasons():
    """게시판을 순회하며 국가별로 가장 최근 조정 공지 하나씩만 골라 사유를 채운다.
    완전히 실패하면(목록 자체를 못 가져오면) None을 반환해서, 호출부가
    "이전 데이터 유지"와 "이번엔 매칭된 국가가 0개" 를 구분할 수 있게 한다."""

    items = []

    try:
        for page in range(1, MAX_PAGES + 1):
            html = fetch_page(LIST_URL, params={"pageIndex": page})
            page_items = parse_list(html)

            print(f"  {page}페이지 매칭 행: {len(page_items)}건")

            if not page_items:
                break

            items.extend(page_items)

    except Exception as e:
        print("여행경보 조정 게시판 목록 접속/파싱 실패:", e)
        return None

    print(f"전체 매칭된 조정 공지 행: {len(items)}건")

    result = {}
    seen_countries = set()

    # 목록은 최신순으로 오는 게 일반적이므로, 국가별로 처음 나온(=가장 최근) 것만 사용
    for item in items:
        for country in item["countries"]:

            if country in seen_countries:
                continue

            reason = ""

            try:
                detail_html = fetch_page(item["detail_url"])
                reason = extract_detail_text(detail_html)
            except Exception as e:
                print(f"  {country} 상세 페이지 접속 실패:", e)

            result[country] = {
                "title": item["title"],
                "reason": reason or item["title"],
                "published_at": item["published_at"],
                "detail_url": item["detail_url"],
            }

            seen_countries.add(country)

    missing = [name for name in TARGET_COUNTRIES if name not in result]

    if missing:
        print("참고: 이번 게시판 확인 범위에서 조정 공지를 못 찾은 파견국:", missing)

    return result


def main():

    print("여행경보 조정 사유 수집 시작")

    reasons = build_reasons()

    if reasons is None:
        # scrape_mofa_country_list.py와 같은 원칙: 접속 자체가 실패했으면
        # 빈 값으로 덮어써서 사유가 통째로 사라지게 하지 말고, 이전 데이터를 유지한다.
        previous = load_previous()
        reasons = previous
        print(f"경고: 이번 수집이 실패해서 이전 데이터를 유지합니다 ({len(previous)}개국 보존).")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(reasons, f, ensure_ascii=False, indent=2)

    print("저장된 국가 수:", len(reasons))
    print("저장 파일:", OUTPUT_FILE)
    print("여행경보 조정 사유 수집 완료")


if __name__ == "__main__":
    main()
