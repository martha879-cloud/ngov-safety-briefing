"""
0404.go.kr의 '국가/지역별 정보' 목록 페이지(/ntnSafetyInfo/list)를 스크래핑해서
파견국 20개국의 현재 경보 배지(1~4단계 + 특별여행주의보)를 뽑아낸다.

이 페이지는 TravelAlarmService2 API와 달리 특별여행주의보(t05)까지 포함해서
사실상 모든 국가를 다 갖고 있기 때문에, API가 놓치는 국가(우간다, 키르기스스탄 등)를
보완하는 용도로 쓴다.

결과는 data/processed/mofa_country_levels.json 에 저장되고,
update_data.py가 이 파일을 읽어서 API 결과를 보완한다.
"""

import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from config import COUNTRIES


LIST_URL = "https://0404.go.kr/ntnSafetyInfo/list"
OUTPUT_FILE = Path("data/processed/mofa_country_levels.json")

# 이 페이지의 한글 국가명이 우리 목록과 다른 경우 매핑
NAME_MAPPING = {
    "키르기즈공화국": "키르기스스탄",
}

COUNTRY_NAMES = {c["name"] for c in COUNTRIES}

# t01~t04는 숫자 단계, t05는 특별여행주의보(별도 트랙)
LEVEL_CODES = {"t01": 1, "t02": 2, "t03": 3, "t04": 4}


def fetch_list_page():

    last_error = None

    # 정부 사이트라 가끔 타임아웃/일시적 오류가 나는 경우가 있어서,
    # 한 번 더 재시도해서 일시적인 실패로 인한 빈 결과를 줄인다.
    for attempt in range(2):
        try:
            response = requests.get(LIST_URL, timeout=30, headers={
                "User-Agent": "KOICA-NGO-Safety-Dashboard"
            })
            response.raise_for_status()

            return response.text

        except requests.RequestException as e:
            last_error = e
            print(f"0404.go.kr 요청 실패 (시도 {attempt + 1}/2):", e)

    raise last_error


def parse_country_levels(html):
    """국가/지역별 정보 목록에서 우리 파견국 20개국의 경보 배지를 뽑아낸다."""

    soup = BeautifulSoup(html, "html.parser")

    result = {}

    for link in soup.select("ul.list-country-01 li a"):

        href = link.get("href", "")

        match = re.search(r"/ntnSafetyInfo/(\d+)/detail", href)

        if not match:
            continue

        country_id = match.group(1)

        # 국가명은 <a> 안의 첫 텍스트 노드 (배지 span들은 별도)
        badges = link.find_all("span", class_="caution02")

        # 배지(span) 텍스트를 제외한 순수 국가명만 추출
        name = link.get_text(strip=True)

        for badge in badges:
            name = name.replace(badge.get_text(strip=True), "")

        name = name.strip()
        name = NAME_MAPPING.get(name, name)

        if name not in COUNTRY_NAMES:
            continue

        level_codes = set()

        for badge in badges:
            classes = badge.get("class", [])
            for cls in classes:
                if cls.startswith("t0"):
                    level_codes.add(cls)

        numeric_levels = sorted(
            LEVEL_CODES[c] for c in level_codes if c in LEVEL_CODES
        )

        has_special = "t05" in level_codes

        result[name] = {
            "id": country_id,
            "levels": numeric_levels,
            "has_special": has_special,
            "detail_url": f"https://0404.go.kr/ntnSafetyInfo/{country_id}/detail",
        }

    return result


def load_previous_output():
    """이전 실행에서 저장된 결과를 불러온다. 없으면 빈 dict."""

    if not OUTPUT_FILE.exists():
        return {}

    try:
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def main():

    print("0404.go.kr 국가/지역별 정보 목록 수집 시작")

    try:
        html = fetch_list_page()
        levels = parse_country_levels(html)
    except Exception as e:
        print("0404.go.kr 국가 목록 접속/파싱 실패:", e)
        levels = {}

    print(f"파견국 중 매칭된 국가 수: {len(levels)} / {len(COUNTRIES)}")

    # 스크래핑이 실패했거나(예외) 결과가 비어있으면, 사이트 구조가 바뀐 게 아니라
    # 일시적인 접속 실패일 가능성이 높다. 이럴 때 빈 결과로 덮어써버리면
    # 우간다처럼 API에 아예 없고 이 스크래핑에만 의존하는 국가의 특별여행주의보 정보가
    # 통째로 사라지는 문제가 생긴다 (실제로 반복 발생했던 문제).
    # 그래서 결과가 비어있을 때는 이전에 저장된 값을 그대로 유지한다.
    if not levels:
        previous = load_previous_output()

        if previous:
            print(
                "경고: 이번 수집 결과가 비어있어서 이전 데이터를 그대로 유지합니다 "
                f"(이전 데이터 {len(previous)}개국 보존)."
            )
            levels = previous
        else:
            print("경고: 이번 수집 결과가 비어있고, 이전에 저장된 데이터도 없습니다.")

    missing = [c["name"] for c in COUNTRIES if c["name"] not in levels]
    if missing:
        print("경고: 이 목록에서도 못 찾은 파견국:", missing)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(levels, f, ensure_ascii=False, indent=2)

    print("저장 파일:", OUTPUT_FILE)
    print("0404.go.kr 국가 목록 수집 완료")


if __name__ == "__main__":
    main()
