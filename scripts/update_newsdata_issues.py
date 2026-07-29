"""
NewsData.io(https://newsdata.io)에서 파견국 20개국의 최근 뉴스를 가져와
안전 관련 이슈만 걸러서 docs/data/newsdata_issues.json 으로 저장하는 스크립트.

GNews와 같은 성격의 소스라서, 필터링 철학도 동일하게 맞춘다:
- 제목(title)에서만 안전 키워드를 판단 (요약 필드가 가끔 다른 기사 내용과 섞여오는 걸 방지)
- 교육/화제성/역사적 회고 신호가 있으면 제외
- 최대한 무료 요청 한도(하루 200건) 안에서, 국가당 1회 요청만 사용

무료 플랜은 "latest" 엔드포인트로 최근 48시간 이내 기사만 준다.
"""

import json
import os
from datetime import datetime
from pathlib import Path

import requests

from config import COUNTRIES
from translate_util import translate_to_korean
from time_util import kst_now


# ==========================================
# 기본 설정
# ==========================================

API_KEY = os.getenv("NEWSDATA_API_KEY")

NEWSDATA_URL = "https://newsdata.io/api/1/latest"

MAX_ARTICLES_PER_COUNTRY = 10  # 무료 플랜 1회 요청당 최대치


# ==========================================
# 안전 이슈 키워드 (GNews와 동일한 철학)
# ==========================================

SAFETY_KEYWORDS = [
    "earthquake", "flood", "flooding", "storm", "typhoon", "cyclone",
    "hurricane", "landslide", "wildfire", "volcano", "tsunami", "drought",

    "protest", "demonstration", "riot", "violence", "clash", "conflict",
    "attack", "terror", "shooting", "kidnapping", "crime", "security",

    "cholera", "dengue", "malaria", "outbreak", "epidemic", "disease",
    "health emergency",

    "airport", "flight", "airline", "transport", "road closure",
    "travel disruption",
]

NOISE_KEYWORDS = [
    "goes viral", "viral video", "viral after",

    "award-winning program", "hands-on", "stem program",
    "engineering education", "curriculum", "students tested",
    "science center", "museum", "exhibit", "documentary",
    "workshop", "scholarship", "internship",

    "decades ago", "decades-old", "historical", "anniversary of",
    "commemorat", "memoir", "testimony about abuses during",
    "civil war era",

    "preparedness", "sends medical aid", "donates", "donation of",
]


def get_volunteer_impact(severity):

    if severity == "critical":
        return "봉사단 활동 및 이동 계획을 즉시 재검토할 필요가 있습니다."

    if severity == "high":
        return "현지 활동과 이동에 영향을 줄 수 있어 현지 상황 확인이 우선 필요합니다."

    return "현지 상황을 모니터링하고 활동 전 최신 정보를 확인하세요."


def get_recommended_action(severity):

    if severity in ("critical", "high"):
        return "현지 협력기관 및 담당자와 즉시 상황을 공유하고 활동 지속 여부를 검토하세요."

    return "관련 정보를 확인하고 현지 상황을 계속 모니터링하세요."


def classify_severity(title_lower):

    high_words = ["killed", "death", "deadly", "violent", "attack", "terror", "severe", "emergency"]
    medium_words = ["warning", "alert", "protest", "flood", "storm", "outbreak",
                     "earthquake", "magnitude", "tsunami", "volcano", "typhoon", "cyclone"]

    if any(w in title_lower for w in high_words):
        return "high"

    if any(w in title_lower for w in medium_words):
        return "medium"

    return "low"


def classify_category(title_lower):

    if any(w in title_lower for w in ["earthquake", "flood", "storm", "typhoon", "cyclone", "hurricane", "landslide", "wildfire", "volcano", "tsunami", "drought"]):
        return "natural_disaster"

    if any(w in title_lower for w in ["cholera", "dengue", "malaria", "outbreak", "epidemic", "disease"]):
        return "health"

    if any(w in title_lower for w in ["protest", "demonstration", "riot", "violence", "clash", "conflict", "attack", "terror", "shooting"]):
        return "conflict"

    if any(w in title_lower for w in ["kidnapping", "crime", "security"]):
        return "security"

    if any(w in title_lower for w in ["airport", "flight", "airline", "transport"]):
        return "transport"

    return "official_notice"


def fetch_country_news(country_code):

    params = {
        "apikey": API_KEY,
        "country": country_code.lower(),
        "language": "en",
        "size": MAX_ARTICLES_PER_COUNTRY,
    }

    response = requests.get(NEWSDATA_URL, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()

    return data.get("results", [])


def build_issues():

    if not API_KEY:
        print("NEWSDATA_API_KEY가 설정되지 않았습니다.")
        return []

    issues = []
    seen_urls = set()

    for country in COUNTRIES:

        print(f"뉴스 검색(NewsData.io): {country['name']}")

        try:
            articles = fetch_country_news(country["code"])
        except requests.RequestException as e:
            print(f"  {country['name']} 검색 실패:", e)
            continue

        print(f"  검색 결과: {len(articles)}건")

        for article in articles:

            title = article.get("title", "") or ""
            description = article.get("description", "") or ""
            link = article.get("link", "") or ""
            title_lower = title.lower()

            if not title or not link:
                continue

            # NewsData.io는 country 파라미터로 이미 그 나라 현지 언론사 기사를 주기 때문에
            # (GNews처럼 해외 언론이 "케냐에서~"라고 쓰는 것과 다르게, 케냐 현지 신문은
            #  제목에 굳이 "케냐"라고 안 씀), 제목에 국가명이 있어야 한다는 조건은 걸지 않는다.

            # 제목에서만 안전 키워드 판단
            if not any(k in title_lower for k in SAFETY_KEYWORDS):
                continue

            combined_text = f"{title} {description}".lower()

            if any(k in combined_text for k in NOISE_KEYWORDS):
                continue

            if link in seen_urls:
                continue

            seen_urls.add(link)

            severity = classify_severity(title_lower)
            category = classify_category(title_lower)

            pub_date = article.get("pubDate", "")
            published_at = pub_date[:10] if pub_date else kst_now().strftime("%Y-%m-%d")

            source_name = (
                article.get("source_name")
                or article.get("source_id")
                or "NewsData.io"
            )

            issues.append({
                "id": f"newsdata-{len(issues) + 1:03d}",
                "country": country["name"],
                "category": category,
                "severity": severity,
                "title": translate_to_korean(title),
                "title_en": title,
                "summary": description or "최근 뉴스에서 확인된 안전 관련 정보입니다.",
                "volunteer_impact": get_volunteer_impact(severity),
                "recommended_action": get_recommended_action(severity),
                "published_at": published_at,
                "source": source_name,
                "source_url": link,
            })

    return issues


def main():

    print("NewsData.io 안전 이슈 수집 시작")

    issues = build_issues()

    issues.sort(key=lambda item: item["published_at"], reverse=True)

    output_file = Path("docs/data/newsdata_issues.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    output = {
        "updated": kst_now().strftime("%Y-%m-%d %H:%M"),
        "issues": issues,
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("NewsData.io 기반 안전 이슈:", len(issues))
    print("저장 파일:", output_file)
    print("NewsData.io 안전 이슈 업데이트 완료")


if __name__ == "__main__":
    main()
