import json
import re
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup


# ==========================================
# 기본 설정
# ==========================================

SAFETY_NOTICE_URL = (
    "https://www.0404.go.kr/bbs/safetyNtc/list"
)

BASE_URL = "https://www.0404.go.kr"

OUTPUT_FILE = Path(
    "docs/data/safety_issues.json"
)


# 현재 대시보드 파견국
TARGET_COUNTRIES = [
    "과테말라",
    "도미니카공화국",
    "동티모르",
    "라오스",
    "르완다",
    "말라위",
    "모로코",
    "몽골",
    "방글라데시",
    "베트남",
    "요르단",
    "이집트",
    "인도네시아",
    "캄보디아",
    "케냐",
    "탄자니아",
    "페루",
    "필리핀"
]


# ==========================================
# 안전 이슈 분류
# ==========================================

def classify_category(text):

    text = text.lower()

    disaster_keywords = [
        "지진",
        "태풍",
        "홍수",
        "호우",
        "폭우",
        "폭염",
        "산불",
        "화산",
        "쓰나미",
        "기상",
        "재난"
    ]

    health_keywords = [
        "감염병",
        "전염병",
        "콜레라",
        "말라리아",
        "뎅기",
        "코로나",
        "보건"
    ]

    transport_keywords = [
        "항공",
        "공항",
        "항공편",
        "교통",
        "운항",
        "도로"
    ]

    conflict_keywords = [
        "전쟁",
        "무력",
        "분쟁",
        "공습",
        "미사일",
        "시위",
        "정세",
        "테러",
        "폭동"
    ]

    security_keywords = [
        "범죄",
        "치안",
        "강도",
        "납치",
        "신변"
    ]

    if any(
        keyword in text
        for keyword in disaster_keywords
    ):
        return "natural_disaster"

    if any(
        keyword in text
        for keyword in health_keywords
    ):
        return "health"

    if any(
        keyword in text
        for keyword in transport_keywords
    ):
        return "transport"

    if any(
        keyword in text
        for keyword in conflict_keywords
    ):
        return "conflict"

    if any(
        keyword in text
        for keyword in security_keywords
    ):
        return "security"

    return "official_notice"


def classify_severity(text):

    text = text.lower()

    critical_keywords = [
        "대피",
        "철수",
        "통행금지",
        "무력 충돌",
        "공습",
        "출국 권고"
    ]

    high_keywords = [
        "긴급",
        "위험",
        "강력히 권고",
        "피격",
        "테러"
    ]

    medium_keywords = [
        "주의",
        "유의",
        "시위",
        "태풍",
        "호우",
        "치안"
    ]

    if any(
        keyword in text
        for keyword in critical_keywords
    ):
        return "critical"

    if any(
        keyword in text
        for keyword in high_keywords
    ):
        return "high"

    if any(
        keyword in text
        for keyword in medium_keywords
    ):
        return "medium"

    return "low"


def get_volunteer_impact(
    category,
    severity
):

    if severity == "critical":
        return (
            "봉사단 활동과 이동 계획을 "
            "즉시 재검토할 필요가 있습니다."
        )

    if severity == "high":
        return (
            "현지 활동과 이동에 영향을 줄 수 있어 "
            "우선 확인이 필요합니다."
        )

    if category == "natural_disaster":
        return (
            "기상 및 재난 상황에 따라 "
            "현장 활동 일정이 변경될 수 있습니다."
        )

    if category == "health":
        return (
            "봉사단의 건강관리와 예방조치 "
            "확인이 필요할 수 있습니다."
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
        "외교부 안전공지와 현지 상황을 "
        "지속적으로 확인하세요."
    )


# ==========================================
# 외교부 안전공지 수집
# ==========================================

print("외교부 안전공지 수집 시작")

headers = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(GitHub Actions Safety Dashboard)"
    )
}


response = requests.get(
    SAFETY_NOTICE_URL,
    headers=headers,
    timeout=30
)


print(
    "HTTP Status:",
    response.status_code
)


response.raise_for_status()


soup = BeautifulSoup(
    response.text,
    "html.parser"
)


rows = soup.find_all("tr")


print(
    "HTML table rows:",
    len(rows)
)


issues = []

seen = set()


for row in rows:

    row_text = row.get_text(
        " ",
        strip=True
    )


    if not row_text:
        continue


    matched_countries = []

    for country in TARGET_COUNTRIES:

        if country in row_text:

            matched_countries.append(
                country
            )


    if not matched_countries:
        continue


    link = row.find("a")


    if link is None:
        continue


    title = link.get_text(
        " ",
        strip=True
    )


    if not title:
        continue


    href = link.get(
        "href",
        ""
    )


    if href.startswith("http"):

        source_url = href

    elif href.startswith("/"):

        source_url = (
            BASE_URL + href
        )

    else:

        source_url = (
            BASE_URL
            + "/"
            + href.lstrip("/")
        )


    date_match = re.search(
        r"\d{4}-\d{2}-\d{2}",
        row_text
    )


    if date_match:

        published_at = (
            date_match.group()
        )

    else:

        published_at = (
            datetime.now()
            .strftime("%Y-%m-%d")
        )


    category = classify_category(
        title
    )


    severity = classify_severity(
        title
    )


    for country in matched_countries:

        unique_key = (
            country,
            title,
            published_at
        )


        if unique_key in seen:
            continue


        seen.add(
            unique_key
        )


        issues.append(
            {
                "id": (
                    f"{country}-"
                    f"{published_at}-"
                    f"{len(issues) + 1}"
                ),

                "country": country,

                "category": category,

                "severity": severity,

                "title": title,

                "summary": (
                    "외교부 해외안전여행 "
                    "안전공지에 등록된 "
                    "최근 안전 관련 정보입니다."
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
                    "외교부 해외안전공지"
                ),

                "source_url": (
                    source_url
                )
            }
        )


issues.sort(
    key=lambda item: (
        item["published_at"]
    ),
    reverse=True
)


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


print(
    "파견국 관련 안전 이슈:",
    len(issues)
)


print(
    "저장 파일:",
    OUTPUT_FILE
)


print(
    "외교부 안전공지 업데이트 완료"
)
