import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

import requests

from config import COUNTRIES


# ==========================================
# 기본 설정
# ==========================================

API_KEY = os.getenv("GNEWS_API_KEY")

OUTPUT_FILE = Path(
    "docs/data/news_issues.json"
)

GNEWS_URL = (
    "https://gnews.io/api/v4/search"
)

MAX_ARTICLES_PER_COUNTRY = 3


# ==========================================
# 파견국 (config/countries.json이 유일한 원본)
# ==========================================

TARGET_COUNTRIES = {
    c["name"]: c["name_en"] for c in COUNTRIES
}


# ==========================================
# 안전 이슈 키워드
# ==========================================

SAFETY_KEYWORDS = [
    "earthquake",
    "flood",
    "flooding",
    "storm",
    "typhoon",
    "cyclone",
    "hurricane",
    "landslide",
    "wildfire",
    "volcano",
    "tsunami",
    "drought",

    "protest",
    "demonstration",
    "riot",
    "violence",
    "clash",
    "conflict",
    "attack",
    "terror",
    "shooting",
    "kidnapping",
    "crime",
    "security",

    "cholera",
    "dengue",
    "malaria",
    "outbreak",
    "epidemic",
    "disease",
    "health emergency",

    "airport",
    "flight",
    "airline",
    "transport",
    "road closure",
    "travel disruption"
]


# ==========================================
# 분류 함수
# ==========================================

def classify_category(text):

    text = text.lower()

    disaster_words = [
        "earthquake",
        "flood",
        "storm",
        "typhoon",
        "cyclone",
        "hurricane",
        "landslide",
        "wildfire",
        "volcano",
        "tsunami",
        "drought"
    ]

    health_words = [
        "cholera",
        "dengue",
        "malaria",
        "outbreak",
        "epidemic",
        "disease",
        "health emergency"
    ]

    conflict_words = [
        "protest",
        "demonstration",
        "riot",
        "violence",
        "clash",
        "conflict",
        "attack",
        "terror",
        "shooting"
    ]

    security_words = [
        "kidnapping",
        "crime",
        "security",
        "robbery"
    ]

    transport_words = [
        "airport",
        "flight",
        "airline",
        "transport",
        "road closure",
        "travel disruption"
    ]

    if any(
        word in text
        for word in disaster_words
    ):
        return "natural_disaster"

    if any(
        word in text
        for word in health_words
    ):
        return "health"

    if any(
        word in text
        for word in conflict_words
    ):
        return "conflict"

    if any(
        word in text
        for word in security_words
    ):
        return "security"

    if any(
        word in text
        for word in transport_words
    ):
        return "transport"

    return "official_notice"


def classify_severity(text):

    text = text.lower()

    critical_words = [
        "state of emergency",
        "evacuation",
        "mass casualties",
        "major attack",
        "deadly earthquake",
        "civil war"
    ]

    high_words = [
        "killed",
        "death",
        "deadly",
        "violent",
        "attack",
        "terror",
        "severe",
        "emergency"
    ]

    medium_words = [
        "warning",
        "alert",
        "protest",
        "flood",
        "storm",
        "outbreak",
        "disruption",
        "earthquake",
        "magnitude",
        "quake",
        "tsunami",
        "volcano",
        "typhoon",
        "cyclone",
        "landslide"
    ]

    if any(
        word in text
        for word in critical_words
    ):
        return "critical"

    if any(
        word in text
        for word in high_words
    ):
        return "high"

    if any(
        word in text
        for word in medium_words
    ):
        return "medium"

    return "low"


def get_volunteer_impact(
    category,
    severity
):

    if severity == "critical":
        return (
            "봉사단 활동 및 이동 계획을 "
            "즉시 재검토할 필요가 있습니다."
        )

    if severity == "high":
        return (
            "현지 활동과 이동에 영향을 줄 수 있어 "
            "현지 상황 확인이 우선 필요합니다."
        )

    if category == "natural_disaster":
        return (
            "기상 및 재난 상황에 따라 "
            "현장 활동과 이동 일정이 "
            "변경될 수 있습니다."
        )

    if category == "health":
        return (
            "봉사단 건강관리 및 "
            "예방조치 확인이 필요할 수 있습니다."
        )

    if category == "transport":
        return (
            "항공 및 현지 이동 일정에 "
            "영향이 있을 수 있습니다."
        )

    return (
        "현지 상황을 모니터링하고 "
        "활동 전 최신 정보를 확인하세요."
    )


def get_recommended_action(
    severity
):

    if severity == "critical":
        return (
            "현지 협력기관 및 담당자와 "
            "즉시 상황을 공유하고 "
            "활동 지속 여부를 검토하세요."
        )

    if severity == "high":
        return (
            "현지 담당자에게 최신 상황을 확인하고 "
            "불필요한 이동을 줄이세요."
        )

    if severity == "medium":
        return (
            "현지 협력기관과 상황을 공유하고 "
            "활동 전 안전 상황을 확인하세요."
        )

    return (
        "관련 정보를 확인하고 "
        "현지 상황을 계속 모니터링하세요."
    )


# ==========================================
# API 키 확인
# ==========================================

if not API_KEY:

    print(
        "GNEWS_API_KEY가 설정되지 않았습니다."
    )

    raise SystemExit(1)


# ==========================================
# 뉴스 수집
# ==========================================

print(
    "GNews 안전 이슈 수집 시작"
)


issues = []

seen_urls = set()


# 최근 7일 기사만 검색
from_date = (
    datetime.utcnow()
    - timedelta(days=7)
).strftime(
    "%Y-%m-%dT00:00:00Z"
)


for korean_name, english_name in (
    TARGET_COUNTRIES.items()
):

    print(
        f"뉴스 검색: {korean_name}"
    )

    query = (
        f'"{english_name}" '
        "earthquake OR flood OR storm "
        "OR typhoon OR protest OR conflict "
        "OR violence OR attack OR crime "
        "OR dengue OR cholera OR outbreak"
    )

    params = {
        "q": query,
        "lang": "en",
        "max": MAX_ARTICLES_PER_COUNTRY,
        "from": from_date,
        "sortby": "publishedAt",
        "apikey": API_KEY
    }

    try:

        response = requests.get(
            GNEWS_URL,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

    except requests.RequestException as error:

        print(
            f"{korean_name} 검색 실패:",
            error
        )

        continue


    articles = data.get(
        "articles",
        []
    )


    print(
        f"  검색 결과: {len(articles)}건"
    )


    for article in articles:

        title = (
            article.get(
                "title",
                ""
            )
        )

        description = (
            article.get(
                "description",
                ""
            )
        )

        article_url = (
            article.get(
                "url",
                ""
            )
        )

    combined_text = (
            f"{title} {description}"
        ).lower()

        title_lower = title.lower()


        # 기사 제목에 해당 국가명이 없으면 제외.
        # (본문에서 다른 나라 기사 하다가 비교삼아 스쳐가듯 언급된 경우를
        #  실제 그 나라의 안전 이슈로 착각하는 것을 방지)
        if english_name.lower() not in title_lower:
            continue


        # 안전 키워드가 없는 기사는 제외
        if not any(
            keyword in combined_text
            for keyword in SAFETY_KEYWORDS
        ):
            continue


        # URL 중복 제거
        if article_url in seen_urls:
            continue


        seen_urls.add(
            article_url
        )


        category = (
            classify_category(
                combined_text
            )
        )

        severity = (
            classify_severity(
                combined_text
            )
        )


        published_at = (
            article.get(
                "publishedAt",
                ""
            )
        )


        if published_at:

            published_at = (
                published_at[:10]
            )

        else:

            published_at = (
                datetime.utcnow()
                .strftime(
                    "%Y-%m-%d"
                )
            )


        issues.append(
            {
                "id": (
                    f"news-"
                    f"{len(issues) + 1:03d}"
                ),

                "country": (
                    korean_name
                ),

                "category": (
                    category
                ),

                "severity": (
                    severity
                ),

                "title": (
                    title
                ),

                "summary": (
                    description
                    or
                    "최근 뉴스에서 확인된 "
                    "안전 관련 정보입니다."
                ),

                "volunteer_impact": (
                    get_volunteer_impact(
                        category,
                        severity
                    )
                ),

                "recommended_action": (
                    get_recommended_action(
                        severity
                    )
                ),

                "published_at": (
                    published_at
                ),

                "source": (
                    article
                    .get(
                        "source",
                        {}
                    )
                    .get(
                        "name",
                        "GNews"
                    )
                ),

                "source_url": (
                    article_url
                )
            }
        )


# ==========================================
# 최신순 정렬
# ==========================================

issues.sort(
    key=lambda item: (
        item["published_at"]
    ),
    reverse=True
)


# ==========================================
# JSON 저장
# ==========================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


output = {
    "updated": (
        datetime.now()
        .strftime(
            "%Y-%m-%d %H:%M"
        )
    ),

    "issues": issues
}


with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        output,
        file,
        ensure_ascii=False,
        indent=2
    )


print()

print(
    "뉴스 기반 안전 이슈:",
    len(issues)
)

print(
    "저장 파일:",
    OUTPUT_FILE
)

print(
    "GNews 안전 이슈 업데이트 완료"
)
